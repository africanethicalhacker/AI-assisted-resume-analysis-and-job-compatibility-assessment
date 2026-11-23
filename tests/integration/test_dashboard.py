from app.models.assessment import Assessment, Recommendation
from tests.conftest import login, make_user
from tests.integration.test_assessment_flow import _setup


def test_assessment_stores_gap_and_recommendations(client):
    rid, jid = _setup(client, "d1@example.com")
    client.post("/assessments/", data={"resume_id": rid, "job_id": jid})
    a = Assessment.query.one()
    gap = a.meta["gap"]
    assert {"matched", "partial", "missing"} <= set(gap["skills"])
    assert gap["summary"]["matched"] >= 1
    page = client.get(f"/assessments/{a.id}").data
    assert b"Skill-gap analysis" in page
    for rec in Recommendation.query.all():
        assert 30 <= rec.fit_score <= 100 and rec.evidence_level in {"strong", "moderate", "emerging"}


def test_dashboard_and_api_for_owner(client):
    rid, jid = _setup(client, "d2@example.com")
    client.post("/assessments/", data={"resume_id": rid, "job_id": jid})
    aid = Assessment.query.one().id
    r = client.get("/dashboard")
    assert r.status_code == 200 and b"Assessment dashboard" in r.data and b"chart.umd.min.js" in r.data
    d = client.get("/api/v1/dashboard-data").get_json()
    assert d["latest"]["id"] == aid and len(d["history"]) == 1 and d["quality_score"] is not None
    c = client.get(f"/api/v1/assessments/{aid}/chart-data").get_json()
    assert len(c["components"]) == 5 and 0 <= c["final_score"] <= 100


def test_api_blocks_other_users_and_anonymous(client):
    rid, jid = _setup(client, "d3@example.com")
    client.post("/assessments/", data={"resume_id": rid, "job_id": jid})
    aid = Assessment.query.one().id
    client.post("/auth/logout")
    assert client.get(f"/api/v1/assessments/{aid}/chart-data").status_code in (302, 401)
    make_user("d4@example.com")
    login(client, "d4@example.com")
    assert client.get(f"/api/v1/assessments/{aid}/chart-data").status_code == 404
    assert client.get("/api/v1/dashboard-data").get_json()["latest"] is None      # sees only own data


def test_admin_dashboard_has_no_candidate_data(client):
    make_user("adm9@example.com", role="administrator")
    login(client, "adm9@example.com")
    page = client.get("/dashboard").data
    assert b"System overview" in page and b"Audit log integrity" in page and b"aggregate counts only" in page
    assert client.get("/api/v1/dashboard-data").status_code == 403


def test_dashboard_js_served_under_csp(client):
    r = client.get("/static/js/dashboard.js")
    assert r.status_code == 200 and b"Chart" in r.data
