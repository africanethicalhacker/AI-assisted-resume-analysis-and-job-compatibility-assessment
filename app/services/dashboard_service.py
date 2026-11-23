from ..models.assessment import Assessment
from ..models.profile import CandidateProfile

ORDER = ["skills", "semantic", "education", "experience", "projects_certs"]
LABELS = {"skills": "Technical skills", "semantic": "Semantic similarity", "education": "Education",
          "experience": "Experience", "projects_certs": "Projects and certifications"}


def assessment_chart_data(a: Assessment) -> dict:
    comps = {d.component: d for d in a.details}
    gap = (a.meta or {}).get("gap", {}).get("skills", {})
    summ = (a.meta or {}).get("gap", {}).get("summary", {})
    return {
        "final_score": round(a.final_score, 1),
        "components": [{"key": k, "label": LABELS[k],
                        "score": round(comps[k].score, 1) if comps[k].explanation.get("applicable") else None,
                        "points": round(comps[k].contribution, 1)} for k in ORDER if k in comps],
        "skill_status": {"matched": summ.get("matched", 0), "partial": summ.get("partial", 0),
                         "missing": summ.get("missing_mandatory", 0) + summ.get("missing_preferred", 0) + summ.get("missing_optional", 0)},
        "has_skills": bool(gap.get("applicable")),
    }


def dashboard_data(user) -> dict:
    assessments = Assessment.query.filter_by(user_id=user.id).order_by(Assessment.created_at.asc()).all()
    latest = assessments[-1] if assessments else None
    profile = CandidateProfile.query.filter_by(user_id=user.id).order_by(CandidateProfile.created_at.desc()).first()
    data = {"quality_score": profile.resume_quality_score if profile else None,
            "history": [{"id": a.id, "date": a.created_at.strftime("%Y-%m-%d %H:%M"), "score": round(a.final_score, 1),
                         "job": (a.meta or {}).get("job_title", "Job")} for a in assessments[-20:]],
            "latest": None}
    if latest:
        d = assessment_chart_data(latest)
        gap = (latest.meta or {}).get("gap", {})
        missing = gap.get("skills", {}).get("missing", {})
        d.update(id=latest.id, job=(latest.meta or {}).get("job_title", "Job"),
                 missing_mandatory=[m["skill"] for m in missing.get("mandatory", [])],
                 missing_preferred=[m["skill"] for m in missing.get("preferred", [])],
                 roles=[{"role": r.role_name, "fit": r.fit_score, "level": r.evidence_level}
                        for r in sorted(latest.recommendations, key=lambda r: r.rank)])
        data["latest"] = d
    return data
