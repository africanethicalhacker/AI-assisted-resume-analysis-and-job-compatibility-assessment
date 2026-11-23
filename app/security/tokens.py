"""Signed, expiring, single-use password-reset tokens (itsdangerous ships with Flask)."""
import hashlib

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

_SALT = "password-reset-v1"


def _fingerprint(password_hash: str) -> str:
    return hashlib.sha256(password_hash.encode()).hexdigest()[:16]


def make_reset_token(secret_key: str, user_id: int, password_hash: str) -> str:
    return URLSafeTimedSerializer(secret_key, salt=_SALT).dumps(
        {"uid": user_id, "fp": _fingerprint(password_hash)})


def read_reset_token(secret_key: str, token: str, max_age: int):
    """Return (user_id, fingerprint) or None."""
    try:
        data = URLSafeTimedSerializer(secret_key, salt=_SALT).loads(token, max_age=max_age)
        return int(data["uid"]), str(data["fp"])
    except (BadSignature, SignatureExpired, KeyError, ValueError, TypeError):
        return None


def fingerprint_matches(password_hash: str, fp: str) -> bool:
    return _fingerprint(password_hash) == fp
