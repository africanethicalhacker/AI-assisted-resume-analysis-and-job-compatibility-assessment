"""Configuration loaded from environment variables. No secrets are hardcoded."""
import base64
import os
import secrets
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, str(default)).split("#")[0].strip().lower()
    return raw in {"1", "true", "yes", "on"}


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "5"))
    MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "instance/uploads")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool("COOKIE_SECURE", False)
    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=int(os.getenv("SESSION_LIFETIME_MINUTES", "30"))
    )
    WTF_CSRF_TIME_LIMIT = 3600

    RATELIMIT_STORAGE_URI = "memory://"  # replace with Redis in production
    RATELIMIT_HEADERS_ENABLED = True

    CLAMD_SOCKET = os.getenv("CLAMD_SOCKET", "")
    CLAMD_HOST = os.getenv("CLAMD_HOST", "")
    CLAMD_PORT = int(os.getenv("CLAMD_PORT", "3310"))

    MAX_RESUMES_PER_USER = int(os.getenv("MAX_RESUMES_PER_USER", "10"))
    RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "90"))
    MAX_UNCOMPRESSED_MB = int(os.getenv("MAX_UNCOMPRESSED_MB", "50"))
    CLAMD_REQUIRED = _bool("CLAMD_REQUIRED", True)
    LOGIN_MAX_FAILURES = int(os.getenv("LOGIN_MAX_FAILURES", "5"))
    LOCKOUT_MINUTES = int(os.getenv("LOCKOUT_MINUTES", "15"))
    ABSOLUTE_SESSION_HOURS = float(os.getenv("ABSOLUTE_SESSION_HOURS", "8"))
    RESET_TOKEN_MAX_AGE = 1800
    RESET_LINK_TO_CONSOLE = False  # dev only: no SMTP in this project

    SBERT_MODEL = os.getenv("SBERT_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    ALLOW_EXTERNAL_AI = _bool("ALLOW_EXTERNAL_AI", False)
    MASTER_KEY_B64 = os.getenv("MASTER_KEY", "")

    @staticmethod
    def master_key_bytes(b64: str) -> bytes:
        key = base64.b64decode(b64)
        if len(key) != 32:
            raise ValueError("MASTER_KEY must decode to exactly 32 bytes (AES-256).")
        return key


class DevelopmentConfig(BaseConfig):
    DEBUG = False
    RESET_LINK_TO_CONSOLE = True


class TestingConfig(BaseConfig):
    TESTING = True
    SECRET_KEY = secrets.token_hex(32)   # random per process; used only by the test configuration
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = True
    RESET_LINK_TO_CONSOLE = False
    CLAMD_REQUIRED = True
    RATELIMIT_ENABLED = False
    MASTER_KEY_B64 = base64.b64encode(b"\x01" * 32).decode()


class ProductionConfig(BaseConfig):
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_NAME = "__Host-session"   # requires Secure, Path=/ and no Domain


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
