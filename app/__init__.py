"""Application factory."""
import hashlib
import logging
import os
import time

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, logout_user

from .config import CONFIGS
from .extensions import csrf, db, limiter, login_manager, migrate
from .security.logging_filter import RedactingFilter

ERROR_MESSAGES = {
    400: "The request could not be understood or its security token was invalid.",
    401: "Please log in.",
    403: "You do not have permission to access this page.",
    404: "The page or record was not found.",
    413: "The uploaded file is too large.",
    429: "Too many requests. Please slow down and try again later.",
}


def build_csp(vendored: bool) -> str:
    cdn = "" if vendored else " https://cdn.jsdelivr.net"
    return (f"default-src 'self'; script-src 'self'{cdn}; style-src 'self'{cdn}; img-src 'self' data:; "
            "font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; "
            "frame-ancestors 'none'; form-action 'self'")


def ua_fingerprint() -> str:
    return hashlib.sha256((request.headers.get("User-Agent", "")).encode()).hexdigest()[:32]


def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(CONFIGS.get(config_name, CONFIGS["development"]))

    if config_name == "production" and not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY must be set in production.")

    redactor = RedactingFilter()
    for logger in (app.logger, logging.getLogger("werkzeug")):
        logger.addFilter(redactor)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.session_protection = "strong"

    from . import models  # noqa: F401  (register tables with SQLAlchemy)
    from .routes import account, admin, api, assessments, auth, board, jobs, main, resumes

    for module in (main, auth, board, resumes, jobs, assessments, api, account, admin):
        app.register_blueprint(module.bp)

    vendor = os.path.join(app.static_folder or "", "vendor")
    vendored = all(os.path.exists(os.path.join(vendor, f)) for f in ("chart.umd.min.js", "bootstrap.min.css"))
    app.config["VENDORED_ASSETS"] = vendored
    csp = build_csp(vendored)

    def _error(exc):
        code = getattr(exc, "code", 500) or 500
        return render_template("errors/error.html", code=code,
                               message=ERROR_MESSAGES.get(code, "Something went wrong.")), code

    for code in ERROR_MESSAGES:
        app.register_error_handler(code, _error)

    @app.before_request
    def enforce_session_limits():
        """Absolute session lifetime and light binding of the session to the browser's User-Agent."""
        if not current_user.is_authenticated:
            return None
        from .security.audit import log_event

        started = session.get("login_at")
        too_old = started is None or time.time() - started > app.config["ABSOLUTE_SESSION_HOURS"] * 3600
        mismatch = session.get("ua_fp") != ua_fingerprint()
        if too_old or mismatch:
            log_event("auth.session_invalid", "denied", user_id=current_user.id,
                      detail="expired" if too_old else "binding_mismatch")
            logout_user()
            session.clear()
            flash("Please log in again.", "info")
            return redirect(url_for("auth.login"))
        return None

    @app.after_request
    def set_security_headers(resp):
        resp.headers["Content-Security-Policy"] = csp
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        resp.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        resp.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        resp.headers["Cache-Control"] = "no-store"
        if app.config["SESSION_COOKIE_SECURE"]:
            resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return resp

    @app.get("/healthz")
    @limiter.exempt
    def healthz():
        return jsonify(status="ok")

    return app
