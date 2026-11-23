from flask import abort, current_app

from ..ai.matching.eligibility import decide
from ..ai.matching.sbert import SbertMatcher
from ..ai.matching.scoring import SCORING_VERSION, score_assessment
from ..ai.matching.similarity import semantic_similarity, strip_flagged_lines
from ..ai.parsing.readers import read_document
from ..ai.recommend.gap import analyse_gap
from ..ai.recommend.roles import recommend_roles
from ..extensions import db
from ..models.assessment import Assessment, AssessmentDetail, Recommendation
from ..models.job import JobDescription
from ..models.resume import Resume
from ..security.audit import log_event
from ..security.rbac import get_owned_or_404
from ..security.sanitise import normalise_text
from . import job_service, profile_service, resume_service, scoring_config
from .taxonomy_service import get_matcher


class AssessmentError(Exception):
    """Message is safe to show to the user."""


def get_sbert() -> SbertMatcher:
    s = current_app.extensions.get("sbert")
    if s is None:
        s = SbertMatcher(current_app.config["SBERT_MODEL"])
        current_app.extensions["sbert"] = s
    return s


def _resume_text(resume, profile) -> str:
    if profile.get("text"):
        return profile["text"]
    return normalise_text(read_document(resume_service.read_plaintext(resume), resume.detected_mime).text)


def _job_for_user(job_id: int, user) -> JobDescription:
    """A candidate may assess against their own jobs and against open jobs posted by an administrator."""
    job = db.session.get(JobDescription, job_id)
    if job is None:
        abort(404)
    if job.user_id == user.id or (job.is_public and job.status == "open"):
        return job
    log_event("authz.denied", "denied", user_id=user.id, resource_type="job_descriptions", resource_id=job_id, detail="not available")
    abort(404)


def run_assessment(user, resume_id: int, job_id: int) -> Assessment:
    resume = get_owned_or_404(Resume, resume_id, user)
    job = _job_for_user(job_id, user)
    if resume.profile is None:
        raise AssessmentError("This resume has not been analysed yet. Open it and click Re-analyse.")
    profile = profile_service.load_profile(resume)
    cfg = scoring_config.load()

    clean_resume, removed = strip_flagged_lines(_resume_text(resume, profile))
    clean_job, removed_job = strip_flagged_lines(job_service.load_text(job))
    reqs = [{"kind": r.kind, "text": r.requirement_text, "strength": r.strength} for r in job.requirements]

    semantic = semantic_similarity(clean_resume, clean_job, cfg["semantic_mode"], get_sbert(), cfg["blend_alpha"])
    result = score_assessment(profile, reqs, scoring_config.fractions(cfg), semantic, get_matcher(), removed + removed_job)

    model_version = f"{SCORING_VERSION}+{semantic['method_used']}" + (f"+{semantic['model']}" if semantic["method_used"] != "tfidf" and semantic["model"] else "")
    a = Assessment(user_id=user.id, profile_id=resume.profile.id, job_id=job.id, final_score=result["final_score"],
                   weights_used=result["weights_configured"], model_version=model_version[:96],
                   meta={"flags": result["flags"], "semantic": semantic, "config": cfg,
                         "n_requirements": len(reqs), "job_title": job.title, "job_public": bool(job.is_public),
                         "gap": analyse_gap(profile, reqs, result["components"]),
                         "eligibility": decide(result["components"], result["final_score"], job.threshold)})
    for rec in recommend_roles(profile):
        a.recommendations.append(Recommendation(
            role_name=rec["role_name"], rank=rec["rank"], fit_score=rec["fit_score"], evidence_level=rec["evidence_level"],
            matching_skills=rec["matching_skills"], missing_skills=rec["missing_skills"],
            suggested_certs=rec["suggested_certs"], roadmap=rec["roadmap"]))
    for c in result["components"]:
        a.details.append(AssessmentDetail(
            component=c["name"], score=c["score"] or 0.0, weight=c["effective_weight"], contribution=c["contribution"],
            explanation={"label": c["label"], "applicable": c["applicable"], "configured_weight": c["configured_weight"],
                         "details": c["explanation"]}))
    db.session.add(a)
    db.session.commit()
    log_event("assessment.run", "success", user_id=user.id, resource_type="assessments", resource_id=a.id,
              detail=f"score={a.final_score} method={semantic['method_used']} flags={len(result['flags'])}")
    return a


def delete_assessment(user, a: Assessment) -> None:
    aid = a.id
    db.session.delete(a)
    db.session.commit()
    log_event("assessment.delete", "success", user_id=user.id, resource_type="assessments", resource_id=aid)
