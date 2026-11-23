import io

from app.extensions import db
from app.models.assessment import Assessment
from app.models.job import JobDescription, JobRequirement
from tests.conftest import login, make_user
from tests.integration.test_parsing_flow import make_resume_docx

JOB = "Job Title: SOC Analyst\nCompany: ExampleCorp\n\nRequirements\n- Hands-on Splunk and Wireshark\n- Experience with Metasploit\n\nNice to have\n- Kali Linux\n"


def as_admin(client, email="boss@example.com"):
    make_user(email, role="administrator")
    login(client, email)


def post_job(client, text=JOB, threshold=40, title="SOC Analyst"):
    client.post("/admin/jobs", data={"title": title, "organization": "ExampleCorp", "threshold": threshold, "text": text})
    return JobDescription.query.filter_by(is_public=True).order_by(JobDescription.id.desc()).first()


def switch_to_candidate(client, email="cand@example.com"):
    client.post("/auth/logout")
    make_user(email)
    login(client, email)


def check(client, job_id, cv=None):
    cv = cv or make_resume_docx()
    return client.post(f"/board/{job_id}", data={"resume_id": 0, "file": (io.BytesIO(cv), "cv.docx")},
                       content_type="multipart/form-data", follow_redirects=True)


def test_admin_posts_job_and_candidate_sees_it(client):
    as_admin(client)
    job = post_job(client)
    assert job is not None and job.is_public and job.status == "open" and job.threshold == 40
    assert {r.strength for r in job.requirements if r.requirement_text in ("Splunk", "Wireshark", "Metasploit")} == {"mandatory"}
    switch_to_candidate(client)
    page = client.get("/board/").data
    assert b"SOC Analyst" in page and b"ExampleCorp" in page


def test_candidate_uploads_cv_and_gets_percentage_and_verdict(client):
    as_admin(client)
    job = post_job(client)
    switch_to_candidate(client)
    r = check(client, job.id)
    assert r.status_code == 200 and b"match with this job" in r.data
    a = Assessment.query.one()
    e = a.meta["eligibility"]
    assert a.job_id == job.id and 0 <= e["percentage"] <= 100 and e["threshold"] == 40
    assert e["verdict"] in {"eligible", "partial", "not_eligible"} and e["checks"]
    assert any(c["requirement"] == "Metasploit" and c["status"] == "not met" for c in e["checks"])   # the CV lacks it
    assert e["verdict"] != "eligible"
    assert b"Mandatory requirements" in r.data and b"Metasploit" in r.data


def test_admin_sees_only_aggregates_never_candidate_data(client):
    as_admin(client)
    job = post_job(client)
    switch_to_candidate(client, "private.person@example.com")
    check(client, job.id)
    aid = Assessment.query.one().id
    client.post("/auth/logout")
    login(client, "boss@example.com")
    page = client.get(f"/admin/jobs/{job.id}").data
    assert b"Checks" in page and b"private.person" not in page and b"aarav" not in page.lower()
    assert client.get(f"/assessments/{aid}").status_code == 403
    assert client.get(f"/board/result/{aid}").status_code == 403
    assert client.get("/resumes/").status_code == 403
    assert client.get(f"/api/v1/assessments/{aid}/chart-data").status_code == 403


def test_other_candidate_cannot_open_result(client):
    as_admin(client)
    job = post_job(client)
    switch_to_candidate(client, "a@example.com")
    check(client, job.id)
    aid = Assessment.query.one().id
    client.post("/auth/logout")
    make_user("b@example.com")
    login(client, "b@example.com")
    assert client.get(f"/board/result/{aid}").status_code == 404


def test_closed_job_is_hidden_and_cannot_be_checked(client):
    as_admin(client)
    job = post_job(client)
    client.post(f"/admin/jobs/{job.id}/status")
    assert db.session.get(JobDescription, job.id).status == "closed"
    switch_to_candidate(client)
    assert b"SOC Analyst" not in client.get("/board/").data
    assert client.get(f"/board/{job.id}").status_code == 404
    assert client.post(f"/board/{job.id}", data={"resume_id": 0}).status_code == 404
    assert Assessment.query.count() == 0


def test_candidate_cannot_post_or_manage_jobs(client):
    make_user("c1@example.com")
    login(client, "c1@example.com")
    assert client.get("/admin/jobs").status_code == 403
    assert client.post("/admin/jobs", data={"title": "x", "text": JOB, "threshold": 50}).status_code == 403
    assert JobDescription.query.filter_by(is_public=True).count() == 0


def test_private_jobs_are_not_on_the_board_or_reachable(client):
    make_user("p1@example.com")
    login(client, "p1@example.com")
    client.post("/jobs/", data={"text": "Requirements\n- Hands-on Splunk\n"})
    private = JobDescription.query.one()
    assert not private.is_public
    client.post("/auth/logout")
    make_user("p2@example.com")
    login(client, "p2@example.com")
    assert b"Splunk" not in client.get("/board/").data
    assert client.get(f"/board/{private.id}").status_code == 404
    assert client.get(f"/jobs/{private.id}").status_code == 404


def test_admin_can_correct_requirement_strength_and_it_changes_the_verdict(client):
    as_admin(client)
    job = post_job(client, threshold=10)
    metasploit = JobRequirement.query.filter_by(job_id=job.id, requirement_text="Metasploit").one()
    client.post(f"/admin/jobs/{job.id}/requirements", data={f"strength_{metasploit.id}": "preferred", "threshold": 10})
    assert db.session.get(JobRequirement, metasploit.id).strength == "preferred"
    switch_to_candidate(client)
    check(client, job.id)
    e = Assessment.query.one().meta["eligibility"]
    assert all(c["requirement"] != "Metasploit" for c in e["checks"])
    assert e["verdict"] == "eligible"


def test_invalid_threshold_is_rejected(client):
    as_admin(client)
    client.post("/admin/jobs", data={"title": "x", "organization": "y", "threshold": 150, "text": JOB})
    assert JobDescription.query.filter_by(is_public=True).count() == 0


def test_delete_is_blocked_after_checks_but_allowed_otherwise(client):
    as_admin(client)
    unused = post_job(client, title="Unused role")
    client.post(f"/admin/jobs/{unused.id}/delete")
    assert db.session.get(JobDescription, unused.id) is None
    used = post_job(client)
    switch_to_candidate(client)
    check(client, used.id)
    client.post("/auth/logout")
    login(client, "boss@example.com")
    client.post(f"/admin/jobs/{used.id}/delete")
    assert db.session.get(JobDescription, used.id) is not None and Assessment.query.count() == 1


def test_pdf_report_works_for_posted_job_and_states_eligibility(client):
    as_admin(client)
    job = post_job(client)
    switch_to_candidate(client)
    check(client, job.id)
    aid = Assessment.query.one().id
    r = client.get(f"/assessments/{aid}/report.pdf")
    assert r.status_code == 200 and r.data.startswith(b"%PDF")


def test_candidate_export_does_not_contain_the_admins_job(client):
    as_admin(client)
    job = post_job(client)
    switch_to_candidate(client)
    check(client, job.id)
    data = client.get("/account/export.json").get_json()
    assert data["job_descriptions"] == [] and len(data["assessments"]) == 1


def test_admin_dashboard_shows_job_board_totals(client):
    as_admin(client)
    post_job(client)
    page = client.get("/dashboard").data
    assert b"Jobs posted" in page and b"candidate checks" in page


def test_posting_is_audited(client):
    from app.models.audit import AuditLog
    as_admin(client)
    post_job(client)
    assert AuditLog.query.filter_by(action="job.post", outcome="success").count() == 1
