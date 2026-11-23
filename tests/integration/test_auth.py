from app.models.audit import AuditLog
from app.models.user import User
from app.security.audit import verify_chain
from tests.conftest import login, make_user


def test_register_creates_candidate_with_argon2id(client):
    r = client.post("/auth/register", data={"email": "A@Example.com", "password": "Correct-Horse-Battery-9",
                                            "confirm": "Correct-Horse-Battery-9"})
    assert r.status_code == 302
    u = User.query.filter_by(email="a@example.com").one()
    assert u.role == "candidate" and u.password_hash.startswith("$argon2id$")


def test_register_ignores_role_injection(client):
    client.post("/auth/register", data={"email": "b@example.com", "password": "Correct-Horse-Battery-9",
                                        "confirm": "Correct-Horse-Battery-9", "role": "administrator"})
    assert User.query.filter_by(email="b@example.com").one().role == "candidate"


def test_login_success_and_generic_failure(client):
    make_user("c@example.com")
    assert login(client, "c@example.com").status_code == 302
    client.post("/auth/logout")
    bad = client.post("/auth/login", data={"email": "c@example.com", "password": "wrong-password-123"})
    unknown = client.post("/auth/login", data={"email": "nobody@example.com", "password": "wrong-password-123"})
    assert b"Invalid credentials" in bad.data and b"Invalid credentials" in unknown.data


def test_lockout_after_repeated_failures(client, app):
    make_user("d@example.com")
    for _ in range(app.config["LOGIN_MAX_FAILURES"]):
        client.post("/auth/login", data={"email": "d@example.com", "password": "wrong-password-123"})
    r = login(client, "d@example.com")          # correct password, but locked
    assert r.status_code == 200
    assert User.query.filter_by(email="d@example.com").one().locked_until is not None


def test_open_redirect_blocked(client):
    make_user("e@example.com")
    r = client.post("/auth/login?next=//evil.example", data={"email": "e@example.com",
                                                             "password": "Correct-Horse-Battery-9"})
    assert "evil.example" not in r.headers["Location"]


def test_protected_page_requires_login(client):
    assert client.get("/dashboard").status_code == 302


def test_audit_chain_verifies_and_detects_tampering(client):
    from app.extensions import db
    make_user("f@example.com")
    login(client, "f@example.com")
    assert verify_chain() == (True, None)
    row = AuditLog.query.order_by(AuditLog.id.asc()).first()
    row.detail = "tampered"
    db.session.commit()
    ok, bad = verify_chain()
    assert not ok and bad == row.id
