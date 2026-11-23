def test_healthz_returns_ok(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_security_headers_present(client):
    resp = client.get("/healthz")
    for header in ("Content-Security-Policy", "X-Content-Type-Options",
                   "X-Frame-Options", "Referrer-Policy"):
        assert header in resp.headers
    assert resp.headers["X-Content-Type-Options"] == "nosniff"


def test_session_cookie_flags(app):
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
