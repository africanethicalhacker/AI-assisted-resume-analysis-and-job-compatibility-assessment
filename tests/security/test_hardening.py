import io
import logging
import os
import re
import time

import pytest

from app.config import BaseConfig, ProductionConfig
from app.models.audit import AuditLog
from app.models.job import JobDescription
from app.models.resume import Resume
from app.models.user import User
from app.security.audit import verify_chain
from app.security.logging_filter import RedactingFilter
from app.security.scanner import ClamAVScanner
from tests.conftest import login, make_user, sample_pdf

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EICAR = r"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"   # harmless, industry-standard AV test string


def test_session_bound_to_user_agent(client):
    make_user("h1@example.com")
    login(client, "h1@example.com")
    assert client.get("/dashboard").status_code == 200
    stolen = client.get("/dashboard", headers={"User-Agent": "Attacker-Browser/1.0"})
    assert stolen.status_code == 302 and "/auth/login" in stolen.headers["Location"]
    assert client.get("/dashboard").status_code == 302          # the session is gone for the real browser as well


def test_absolute_session_timeout(client):
    make_user("h2@example.com")
    login(client, "h2@example.com")
    with client.session_transaction() as sess:
        sess["login_at"] = int(time.time()) - 9 * 3600
    assert client.get("/dashboard").status_code == 302


def test_cross_origin_and_cache_headers(client):
    h = client.get("/auth/login").headers
    assert h["Cross-Origin-Opener-Policy"] == "same-origin" and h["Cross-Origin-Resource-Policy"] == "same-origin"
    assert h["Cache-Control"] == "no-store"
    assert "frame-ancestors 'none'" in h["Content-Security-Policy"] and "unsafe-inline" not in h["Content-Security-Policy"]


def test_production_cookie_hardening():
    assert ProductionConfig.SESSION_COOKIE_SECURE is True
    assert ProductionConfig.SESSION_COOKIE_NAME.startswith("__Host-")
    assert BaseConfig.SESSION_COOKIE_HTTPONLY is True and BaseConfig.SESSION_COOKIE_SAMESITE == "Lax"


def test_redacting_filter_masks_emails():
    rec = logging.LogRecord("x", logging.INFO, "f", 1, "login failed for %s", ("someone@example.com",), None)
    RedactingFilter().filter(rec)
    assert "someone@example.com" not in rec.getMessage() and "[email]" in rec.getMessage()


def test_audit_log_never_contains_email(client):
    make_user("secret.person@example.com")
    login(client, "secret.person@example.com")
    client.post("/auth/login", data={"email": "secret.person@example.com", "password": "bad-password-123"})
    assert all("secret.person" not in (r.detail or "") for r in AuditLog.query.all())


def test_path_traversal_rejected(client, app):
    from app.services.resume_service import UploadError, safe_path
    with pytest.raises(UploadError):
        safe_path("../../etc/passwd")
    assert safe_path("a" * 32).startswith(os.path.realpath(app.config["UPLOAD_DIR"]))


def test_no_external_ai_or_network_clients_in_application_code():
    banned = re.compile(r"^\s*(import|from)\s+(openai|anthropic|requests|httpx|aiohttp|urllib\.request|http\.client)\b", re.M)
    offenders = []
    for dp, _, files in os.walk(os.path.join(ROOT, "app")):
        for f in files:
            if f.endswith(".py") and banned.search(open(os.path.join(dp, f), encoding="utf-8").read()):
                offenders.append(os.path.join(dp, f))
    assert offenders == []                       # resume text never leaves the server


def test_external_ai_disabled_by_default(app):
    assert app.config["ALLOW_EXTERNAL_AI"] is False


def test_export_contains_only_own_data(client):
    make_user("e1@example.com")
    make_user("e2@example.com")
    login(client, "e1@example.com")
    client.post("/jobs/", data={"text": "Requirements\n- Hands-on Splunk\n"})
    client.post("/auth/logout")
    login(client, "e2@example.com")
    client.post("/jobs/", data={"text": "Requirements\n- Hands-on Wireshark and Nmap\n"})
    data = client.get("/account/export.json").get_json()
    assert data["account"]["email"] == "e2@example.com"
    assert len(data["job_descriptions"]) == 1 and "Wireshark" in data["job_descriptions"][0]["text"]
    assert b"e1@example.com" not in client.get("/account/export.json").data
    assert "password" not in str(data).lower()


def test_delete_account_requires_password_and_erases_everything(client, app):
    make_user("del@example.com")
    login(client, "del@example.com")
    client.post("/resumes/", data={"file": (io.BytesIO(sample_pdf()), "cv.pdf")}, content_type="multipart/form-data")
    client.post("/jobs/", data={"text": "Requirements\n- Hands-on Splunk\n"})
    stored = Resume.query.one().stored_name
    path = os.path.join(app.config["UPLOAD_DIR"], stored + ".bin")
    assert os.path.exists(path)
    client.post("/account/delete", data={"password": "wrong-password-123", "confirm": "DELETE"})
    assert User.query.filter_by(email="del@example.com").count() == 1          # wrong password: nothing deleted
    client.post("/account/delete", data={"password": "Correct-Horse-Battery-9", "confirm": "nope"})
    assert User.query.filter_by(email="del@example.com").count() == 1          # missing confirmation: nothing deleted
    client.post("/account/delete", data={"password": "Correct-Horse-Battery-9", "confirm": "DELETE"})
    assert User.query.filter_by(email="del@example.com").count() == 0
    assert Resume.query.count() == 0 and JobDescription.query.count() == 0 and not os.path.exists(path)
    assert verify_chain() == (True, None)                                       # audit trail stays intact


def test_admin_cannot_use_candidate_account_routes(client):
    make_user("adm7@example.com", role="administrator")
    login(client, "adm7@example.com")
    assert client.get("/account/").status_code == 403
    assert client.get("/account/export.json").status_code == 403


def test_sensitive_values_not_in_pages(client):
    u = make_user("s1@example.com")
    login(client, "s1@example.com")
    client.post("/resumes/", data={"file": (io.BytesIO(sample_pdf()), "cv.pdf")}, content_type="multipart/form-data")
    rid = Resume.query.one().id
    page = client.get(f"/resumes/{rid}").data
    for secret in (u.password_hash.encode(), Resume.query.one().wrapped_dek, b"argon2id"):
        assert secret not in page


def test_clamav_detects_eicar_when_available():
    scanner = ClamAVScanner(os.getenv("CLAMD_SOCKET", ""), os.getenv("CLAMD_HOST", ""), int(os.getenv("CLAMD_PORT", "3310")), timeout=10)
    result = scanner.scan(EICAR.encode())
    if result.status == "error":
        pytest.skip("clamd is not reachable from this environment")
    assert result.status == "infected"
