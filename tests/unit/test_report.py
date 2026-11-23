from app.ai.pipeline import analyse_job_text, analyse_resume, score_pair, combine_scores
from app.ai.matching.scoring import DEFAULT_WEIGHTS
from app.ai.recommend.gap import analyse_gap
from app.ai.recommend.roles import recommend_roles
from app.ai.skills.taxonomy import SkillMatcher
from app.reporting.pdf_report import build_pdf
from tests.unit.test_extraction import JD, RESUME

M = SkillMatcher.from_seed()


def make_data(name_override=None):
    profile = analyse_resume(RESUME, M)
    job = analyse_job_text(JD, M)
    res = score_pair(profile, job, M)
    gap = analyse_gap(profile, job["reqs"], res["components"])
    recs = recommend_roles(profile)
    comps = [{"label": c["label"], "score": c["score"] or 0, "applicable": c["applicable"],
              "effective_weight": c["effective_weight"], "contribution": c["contribution"]} for c in res["components"]]
    return {
        "generated_at": "2026-11-09 10:00", "assessment": {"id": 7, "final_score": res["final_score"], "model_version": "hybrid-1.0+tfidf"},
        "candidate": {"name": name_override or profile["name"]["value"], "email": profile["email"]["value"], "phone": None,
                      "links": [], "summary": profile["summary"], "quality_score": profile["quality"]["score"]},
        "extraction": {k: profile[k] for k in ("education", "skills", "certifications", "experience", "internships", "projects", "achievements", "sections_found")}
                      | {"experience_summary": profile["experience_summary"]},
        "job": {"title": job["title"], "organization": job["organization"],
                "requirements": [{"kind": r["kind"], "requirement_text": r["requirement_text"], "strength": r["strength"]} for r in job["requirements"]]},
        "components": comps, "semantic": res["components"][1]["explanation"], "weights_configured": DEFAULT_WEIGHTS, "gap": gap,
        "recommendations": recs, "flags": res["flags"]}


def test_pdf_contains_all_twelve_sections():
    pdf = build_pdf(make_data(), unicode_font=False, compress=False)
    assert pdf.startswith(b"%PDF") and pdf.rstrip().endswith(b"%%EOF")
    for title in ("Candidate summary", "Resume extraction results", "Job description summary", "Compatibility score",
                  "Component-wise scoring", "Matching skills", "Missing skills", "Education analysis",
                  "Experience analysis", "Recommendations", "Scoring methodology", "Assessment limitations"):
        assert title.encode() in pdf, title
    assert b"Aarav Sharma" in pdf and b"Splunk" in pdf


def test_pdf_survives_hostile_markup_and_unicode():
    hostile = "<b>unclosed & <i>x</para> <script>alert(1)</script>"
    assert build_pdf(make_data(hostile), unicode_font=False).startswith(b"%PDF")      # would raise if markup were not escaped
    assert build_pdf(make_data("अनन्या शर्मा Zoë"), unicode_font=True).startswith(b"%PDF")


def test_pdf_has_chart_image_and_reasonable_size():
    pdf = build_pdf(make_data())
    assert b"/Subtype /Image" in pdf or b"/Image" in pdf
    assert 10_000 < len(pdf) < 3_000_000


def test_combine_scores_matches_scoring_engine():
    profile, job = analyse_resume(RESUME, M), analyse_job_text(JD, M)
    res = score_pair(profile, job, M)
    scores = {c["name"]: c["score"] for c in res["components"]}
    assert abs(combine_scores(scores, DEFAULT_WEIGHTS) - res["final_score"]) < 0.02
