from datetime import timedelta

from flask import current_app, url_for
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models.mixins import utcnow
from ..models.user import User
from ..security import passwords, tokens
from ..security.audit import log_event


class AuthError(Exception):
    """Message is safe to show to the user."""


def normalise_email(email: str) -> str:
    return (email or "").strip().lower()


def register_user(email: str, password: str) -> User:
    email = normalise_email(email)
    errors = passwords.validate_password(password, email)
    if errors:
        raise AuthError(" ".join(errors))
    user = User(email=email, password_hash=passwords.hash_password(password), role="candidate")
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        log_event("auth.register", "failure", detail="duplicate")
        # Deliberately generic: do not confirm whether the email already exists.
        raise AuthError("Registration could not be completed with these details.")
    log_event("auth.register", "success", user_id=user.id)
    return user


def authenticate(email: str, password: str):
    """Return (user_or_None, reason). `reason` is for the audit log only, never shown to users."""
    cfg = current_app.config
    user = User.query.filter_by(email=normalise_email(email)).first()
    now = utcnow()
    if user is None:
        passwords.verify_dummy(password)
        log_event("auth.login", "failure", detail="unknown_user")
        return None, "unknown_user"
    if user.locked_until and user.locked_until > now:
        passwords.verify_dummy(password)
        log_event("auth.login", "denied", user_id=user.id, detail="locked")
        return None, "locked"
    if not user.is_active:
        passwords.verify_dummy(password)
        log_event("auth.login", "denied", user_id=user.id, detail="inactive")
        return None, "inactive"
    if passwords.verify_password(user.password_hash, password):
        user.failed_logins, user.locked_until, user.last_login_at = 0, None, now
        if passwords.needs_rehash(user.password_hash):
            user.password_hash = passwords.hash_password(password)
        db.session.commit()
        log_event("auth.login", "success", user_id=user.id)
        return user, "ok"
    user.failed_logins += 1
    if user.failed_logins >= cfg["LOGIN_MAX_FAILURES"]:
        user.locked_until = now + timedelta(minutes=cfg["LOCKOUT_MINUTES"])
        user.failed_logins = 0
        log_event("auth.lockout", "denied", user_id=user.id)
    db.session.commit()
    log_event("auth.login", "failure", user_id=user.id, detail="bad_password")
    return None, "bad_password"


def request_password_reset(email: str) -> None:
    """Always behaves identically to the caller; the link is delivered out of band."""
    user = User.query.filter_by(email=normalise_email(email)).first()
    if user is None or not user.is_active:
        log_event("auth.reset_request", "failure", detail="no_account")
        return
    token = tokens.make_reset_token(current_app.config["SECRET_KEY"], user.id, user.password_hash)
    log_event("auth.reset_request", "success", user_id=user.id)
    if current_app.config["RESET_LINK_TO_CONSOLE"]:
        # DEVELOPMENT ONLY. A real deployment must send this by email over TLS.
        print("PASSWORD RESET LINK (dev only):", url_for("auth.reset", token=token, _external=True))


def reset_password(token: str, new_password: str) -> None:
    cfg = current_app.config
    parsed = tokens.read_reset_token(cfg["SECRET_KEY"], token, cfg["RESET_TOKEN_MAX_AGE"])
    user = db.session.get(User, parsed[0]) if parsed else None
    if user is None or not tokens.fingerprint_matches(user.password_hash, parsed[1]):
        log_event("auth.reset", "failure", detail="bad_token")
        raise AuthError("This reset link is invalid or has expired.")
    errors = passwords.validate_password(new_password, user.email)
    if errors:
        raise AuthError(" ".join(errors))
    user.password_hash = passwords.hash_password(new_password)
    user.failed_logins, user.locked_until = 0, None
    db.session.commit()
    log_event("auth.reset", "success", user_id=user.id)
