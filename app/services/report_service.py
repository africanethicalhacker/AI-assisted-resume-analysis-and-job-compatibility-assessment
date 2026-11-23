from datetime import datetime, timezone

from flask import abort

from ..extensions import db
from ..models.assessment import Assessment
from ..models.job import JobDescription
from ..models.profile import CandidateProfile
from ..reporting.pdf_report import build_pdf
from ..security.audit import log_event
from . import profile_service

_ORDER = ["skills", "semantic", "education", "experience", "projects_certs"]


def build_report_data(user, a: Assessment) -> dict:
    prow = db.session.get(CandidateProfile, a.profile_id)
    job = db.session.get(JobDescription, a.job_id)
    if prow is None or job is None or prow.user_id != user.id or (job.user_id != user.id and not job.is_public):
        abort(404)
    profile = profile_service.load_profile(prow.resume)
    meta = a.meta or {}
    comps = []
    for d in sorted(a.details, key=lambda d: _ORDER.index(d.component) if d.component in _ORDER else 99):
        ex = d.explanation or {}
        comps.append({"label": ex.get("label", d.component), "score": d.score, "applicable": ex.get("applicable", True),
                      "effective_weight": d.weight, "contribution": d.contribution})
    links = [l["value"] for l in profile.get("links", [])]
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "assessment": {"id": a.id, "final_score": a.final_score, "model_version": a.model_version},
        "candidate": {"name": (profile.get("name") or {}).get("value"), "email": (profile.get("email") or {}).get("value"),
                      "phone": (profile.get("phone") or {}).get("value"), "links": links, "summary": profile.get("summary"),
                      "quality_score": prow.resume_quality_score},
        "extraction": {k: profile.get(k, []) for k in ("education", "skills", "certifications", "experience", "internships", "projects", "achievements", "sections_found")}
                      | {"experience_summary": profile.get("experience_summary", {})},
        "job": {"title": job.title, "organization": job.organization,
                "requirements": [{"kind": r.kind, "requirement_text": r.requirement_text, "strength": r.strength} for r in job.requirements]},
        "components": comps, "semantic": meta.get("semantic", {}), "weights_configured": a.weights_used, "gap": meta.get("gap", {}),
        "recommendations": [{"rank": r.rank, "role_name": r.role_name, "fit_score": r.fit_score, "evidence_level": r.evidence_level,
                             "matching_skills": r.matching_skills or [], "missing_skills": r.missing_skills or [],
                             "suggested_certs": r.suggested_certs or [], "roadmap": r.roadmap or []}
                            for r in sorted(a.recommendations, key=lambda r: r.rank)],
        "flags": meta.get("flags", []), "eligibility": meta.get("eligibility"),
    }


def make_pdf(user, a: Assessment) -> bytes:
    pdf = build_pdf(build_report_data(user, a))
    log_event("report.download", "success", user_id=user.id, resource_type="assessments", resource_id=a.id, detail=f"bytes={len(pdf)}")
    return pdf
