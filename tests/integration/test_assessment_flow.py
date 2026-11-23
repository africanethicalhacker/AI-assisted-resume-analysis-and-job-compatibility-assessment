import io

from app.models.assessment import Assessment
from app.models.job import JobDescription
from app.models.resume import Resume
from tests.conftest import login, make_user
from tests.integration.test_parsing_flow import make_resume_docx

JD = "SOC Analyst\n\nRequirements\n- Hands-on Splunk and Wireshark\n- 2+ years of experience\n- Bachelor's degree in computer science\n\nNice to have\n- Kali Linux\n"


def _setup(client, email):
    make_user(email)
    login(client, email)
    client.post("/resumes/", data={"file": (io.BytesIO(make_resume_docx()), "cv.docx")}, content_type="multipart/form-data")
    client.post("/jobs/", data={"text": JD})
    return Resume.query.filter_by().all()[-1].id, JobDescription.query.all()[-1].id


def test_assessment_end_to_end(client):
    rid, jid = _setup(client, "as1@example.com")
    r = client.post("/assessments/", data={"resume_id": rid, "job_id": jid}, follow_redirects=True)
    assert r.status_code == 200 and b"Compatibility score" in r.data
    a = Assessment.query.one()
    assert 0 <= a.final_score <= 100
    assert len(a.details) == 5
    assert abs(sum(d.contribution for d in a.details) - a.final_score) < 0.05
    assert a.weights_used["skills"] == 0.35 and "hybrid-1.0" in a.model_version
    assert a.meta["flags"]                                    # resume contains an injection line -> flagged, not obeyed
    page = client.get(f"/assessments/{a.id}").data
    assert b"Splunk" in page and b"matched" in page


def test_other_users_cannot_use_or_view_assessment(client):
    rid, jid = _setup(client, "as2@example.com")
    client.post("/assessments/", data={"resume_id": rid, "job_id": jid})
    aid = Assessment.query.one().id
    client.post("/auth/logout")
    make_user("as3@example.com")
    login(client, "as3@example.com")
    assert client.get(f"/assessments/{aid}").status_code == 404
    assert client.post(f"/assessments/{aid}/delete").status_code == 404
    client.post("/assessments/", data={"resume_id": rid, "job_id": jid})   # not in this user's choices -> rejected
    assert Assessment.query.count() == 1


def test_admin_can_change_weights_and_invalid_sum_rejected(client, app):
    make_user("adm3@example.com", role="administrator")
    login(client, "adm3@example.com")
    good = {"skills": 50, "semantic": 20, "education": 10, "experience": 10, "projects_certs": 10,
            "semantic_mode": "tfidf", "blend_alpha": 0.5}
    client.post("/admin/scoring", data=good)
    from app.services import scoring_config
    assert scoring_config.load()["weights"]["skills"] == 50 and scoring_config.load()["semantic_mode"] == "tfidf"
    client.post("/admin/scoring", data={**good, "skills": 60})            # totals 110
    assert scoring_config.load()["weights"]["skills"] == 50


def test_candidate_cannot_open_scoring_admin(client):
    make_user("c9@example.com")
    login(client, "c9@example.com")
    assert client.get("/admin/scoring").status_code == 403
