"""Argon2id password hashing and a NIST SP 800-63B style password policy."""
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_ph = PasswordHasher()  # argon2-cffi defaults to Argon2id
_DUMMY_HASH = _ph.hash("timing-equalisation-placeholder")

_COMMON = {
    "password1234", "123456789012", "qwertyuiop12", "iloveyou1234", "administrator",
    "welcome12345", "letmein12345", "passwordpassword", "changeme1234", "abcdefghijkl",
}
MIN_LEN, MAX_LEN = 12, 128


def validate_password(password: str, email: str = "") -> list:
    errors = []
    if len(password) < MIN_LEN:
        errors.append(f"Password must be at least {MIN_LEN} characters.")
    if len(password) > MAX_LEN:
        errors.append(f"Password must be at most {MAX_LEN} characters.")
    if password.lower() in _COMMON or len(set(password)) < 5:
        errors.append("Password is too common or too repetitive.")
    local = email.split("@")[0].lower() if email else ""
    if len(local) >= 4 and local in password.lower():
        errors.append("Password must not contain your email name.")
    return errors


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(stored_hash: str, password: str) -> bool:
    try:
        return _ph.verify(stored_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def verify_dummy(password: str) -> None:
    """Spend the same time as a real check so unknown users are not distinguishable by timing."""
    verify_password(_DUMMY_HASH, password)


def needs_rehash(stored_hash: str) -> bool:
    try:
        return _ph.check_needs_rehash(stored_hash)
    except InvalidHashError:
        return True
