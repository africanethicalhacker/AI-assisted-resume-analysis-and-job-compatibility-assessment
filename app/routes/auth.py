import time
from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, session, url_for, request
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import limiter
from ..forms import LoginForm, RegisterForm, ResetForm, ResetRequestForm
from ..security.audit import log_event
from ..services import auth_service
from ..services.auth_service import AuthError

bp = Blueprint("auth", __name__, url_prefix="/auth")


def _is_safe_next(target) -> bool:
    if not target or "\\" in target or not target.startswith("/") or target.startswith("//"):
        return False
    parsed = urlparse(target)
    return not parsed.scheme and not parsed.netloc


@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            auth_service.register_user(form.email.data, form.password.data)
        except AuthError as exc:
            flash(str(exc), "danger")
        else:
            flash("Account created. Please log in.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user, _reason = auth_service.authenticate(form.email.data, form.password.data)
        if user:
            session.clear()  # prevent session fixation
            login_user(user)
            session.permanent = True
            session["login_at"] = int(time.time())
            from .. import ua_fingerprint
            session["ua_fp"] = ua_fingerprint()
            nxt = request.args.get("next")
            return redirect(nxt if _is_safe_next(nxt) else url_for("main.dashboard"))
        # One message for every failure mode: no account or lockout enumeration.
        flash("Invalid credentials, or the account is temporarily locked.", "danger")
    return render_template("auth/login.html", form=form)


@bp.post("/logout")
@login_required
def logout():
    log_event("auth.logout", "success", user_id=current_user.id)
    logout_user()
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@bp.route("/reset", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def reset_request():
    form = ResetRequestForm()
    if form.validate_on_submit():
        auth_service.request_password_reset(form.email.data)
        flash("If that account exists, a reset link has been issued.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_request.html", form=form)


@bp.route("/reset/<token>", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def reset(token):
    form = ResetForm()
    if form.validate_on_submit():
        try:
            auth_service.reset_password(token, form.password.data)
        except AuthError as exc:
            flash(str(exc), "danger")
        else:
            flash("Password updated. Please log in.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/reset.html", form=form)
