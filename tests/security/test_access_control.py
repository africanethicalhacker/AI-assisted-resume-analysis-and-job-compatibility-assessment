import io

from app.models.resume import Resume
from tests.conftest import login, make_user, sample_pdf


def _upload(client):
    client.post("/resumes/", data={"file": (io.BytesIO(sample_pdf()), "cv.pdf")},
                content_type="multipart/form-data")


def test_idor_other_users_resume_is_404(client, app):
    make_user("alice@example.com")
    make_user("bob@example.com")
    login(client, "alice@example.com")
    _upload(client)
    rid = Resume.query.one().id
    client.post("/auth/logout")
    login(client, "bob@example.com")
    assert client.get(f"/resumes/{rid}").status_code == 404
    assert client.post(f"/resumes/{rid}/delete").status_code == 404
    assert Resume.query.count() == 1


def test_candidate_cannot_reach_admin(client):
    make_user("cand@example.com")
    login(client, "cand@example.com")
    assert client.get("/admin/").status_code == 403


def test_admin_cannot_read_resume_content_pages(client):
    make_user("adm@example.com", role="administrator")
    login(client, "adm@example.com")
    assert client.get("/resumes/").status_code == 403
    assert client.get("/admin/").status_code == 200


def test_anonymous_blocked_everywhere(client):
    for url in ("/resumes/", "/resumes/1", "/admin/", "/dashboard"):
        assert client.get(url).status_code in (302, 401)


def test_csrf_enforced_when_enabled(app):
    app.config["WTF_CSRF_ENABLED"] = True
    c = app.test_client()
    r = c.post("/auth/login", data={"email": "x@example.com", "password": "whatever-123456"})
    assert r.status_code == 400


def test_sql_injection_in_login_is_inert(client):
    make_user("sqli@example.com")
    r = client.post("/auth/login", data={"email": "' OR '1'='1' --", "password": "' OR '1'='1"})
    assert r.status_code == 200 and b"Invalid credentials" in r.data


def test_xss_in_filename_is_escaped(client):
    make_user("xss@example.com")
    login(client, "xss@example.com")
    client.post("/resumes/", data={"file": (io.BytesIO(sample_pdf()), "<script>alert(1)</script>.pdf")},
                content_type="multipart/form-data")
    page = client.get("/resumes/").data
    assert b"<script>alert(1)</script>" not in page


def test_security_headers_on_every_response(client):
    r = client.get("/auth/login")
    assert r.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in r.headers["Content-Security-Policy"]
