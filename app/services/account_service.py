"""Data-subject rights: export everything the system holds about a user, and erase it."""
from datetime import datetime, timezone

from ..extensions import db
from ..models.assessment import Assessment
from ..models.job import JobDescription
from ..models.resume import Resume
from ..security import passwords
from ..security.audit import log_event
from . import job_service, profile_service, resume_service
from .auth_service import AuthError


def export_user_data(user) -> dict:
    resumes = []
    for r in Resume.query.filter_by(user_id=user.id).order_by(Resume.uploaded_at).all():
        profile = profile_service.load_profile(r)
        if profile:
            profile = {k: v for k, v in profile.items() if k != "text"}
        resumes.append({"id": r.id, "file_name": resume_service.display_name(r), "uploaded_at": r.uploaded_at.isoformat(),
                        "size_bytes": r.size_bytes, "sha256": r.sha256, "scan_status": r.scan_status,
                        "scheduled_deletion": r.delete_after.isoformat(), "profile": profile})
    jobs = [{"id": j.id, "title": j.title, "organization": j.organization, "created_at": j.created_at.isoformat(),
             "text": job_service.load_text(j),
             "requirements": [{"kind": q.kind, "text": q.requirement_text, "strength": q.strength} for q in j.requirements]}
            for j in JobDescription.query.filter_by(user_id=user.id).order_by(JobDescription.created_at).all()]
    assessments = [{"id": a.id, "job_id": a.job_id, "profile_id": a.profile_id, "final_score": a.final_score,
                    "weights_used": a.weights_used, "model_version": a.model_version, "created_at": a.created_at.isoformat(),
                    "components": [{"component": d.component, "score": d.score, "weight": d.weight, "contribution": d.contribution}
                                   for d in a.details],
                    "recommendations": [{"role": r.role_name, "rank": r.rank, "fit_score": r.fit_score} for r in a.recommendations]}
                   for a in Assessment.query.filter_by(user_id=user.id).order_by(Assessment.created_at).all()]
    log_event("account.export", "success", user_id=user.id)
    return {"exported_at": datetime.now(timezone.utc).isoformat(),
            "account": {"email": user.email, "role": user.role, "created_at": user.created_at.isoformat()},
            "resumes": resumes, "job_descriptions": jobs, "assessments": assessments}


def delete_account(user, password: str) -> None:
    if not passwords.verify_password(user.password_hash, password):
        log_event("account.delete", "denied", user_id=user.id, detail="bad_password")
        raise AuthError("The password is incorrect.")
    uid = user.id
    for a in Assessment.query.filter_by(user_id=uid).all():
        db.session.delete(a)
    for j in JobDescription.query.filter_by(user_id=uid).all():
        db.session.delete(j)
    db.session.flush()
    for r in Resume.query.filter_by(user_id=uid).all():
        resume_service._remove_blob(r.stored_name)
        db.session.delete(r)
    db.session.flush()
    db.session.delete(user)
    db.session.commit()
    log_event("account.delete", "success", detail=f"uid={uid}")   # audit rows are kept; they hold no personal data
