"""System overview for administrators. Aggregates only: no resume, job or profile content."""
from datetime import timedelta

from sqlalchemy import func

from ..extensions import db
from ..models.assessment import Assessment
from ..models.audit import AuditLog
from ..models.job import JobDescription
from ..models.mixins import utcnow
from ..models.profile import Skill
from ..models.resume import Resume
from ..models.user import User
from ..security.audit import verify_chain
from ..security.scanner import get_scanner
from . import scoring_config


def _scanner_status() -> str:
    try:
        scanner = get_scanner()
        ping = getattr(scanner, "_client", None)
        if ping is None:                       # test doubles
            return "online"
        return "online" if ping().ping() == "PONG" else "offline"
    except Exception:  # noqa: BLE001
        return "offline"


def _sbert_status(app_extensions) -> str:
    s = app_extensions.get("sbert")
    if s is None:
        return "not loaded yet (loads on first assessment)"
    return "loaded" if getattr(s, "_encoder", None) is not None else "not loaded yet (loads on first assessment)"


def overview(app_extensions) -> dict:
    now = utcnow()
    day = now - timedelta(hours=24)
    ok, bad_id = verify_chain()
    q = lambda *c: db.session.query(*c)
    avg = q(func.avg(Assessment.final_score)).scalar()
    cfg = scoring_config.load()
    failed = AuditLog.query.filter(AuditLog.created_at >= day, AuditLog.action == "auth.login",
                                   AuditLog.outcome.in_(["failure", "denied"])).count()
    return {
        "users": {"total": User.query.count(), "candidates": User.query.filter_by(role="candidate").count(),
                  "administrators": User.query.filter_by(role="administrator").count(),
                  "locked": User.query.filter(User.locked_until > now).count()},
        "data": {"resumes": Resume.query.count(), "jobs": JobDescription.query.count(),
                 "postings_open": JobDescription.query.filter_by(is_public=True, status="open").count(),
                 "postings_total": JobDescription.query.filter_by(is_public=True).count(),
                 "checks_on_postings": Assessment.query.join(JobDescription, Assessment.job_id == JobDescription.id).filter(JobDescription.is_public.is_(True)).count(), "assessments": Assessment.query.count(),
                 "avg_score": round(avg, 1) if avg is not None else None, "skills": Skill.query.filter_by(is_active=True).count(),
                 "expiring_7d": Resume.query.filter(Resume.delete_after < now + timedelta(days=7)).count()},
        "activity_24h": {"events": AuditLog.query.filter(AuditLog.created_at >= day).count(), "failed_logins": failed,
                         "uploads_rejected": AuditLog.query.filter(AuditLog.created_at >= day, AuditLog.action == "resume.upload",
                                                                  AuditLog.outcome == "rejected").count(),
                         "access_denied": AuditLog.query.filter(AuditLog.created_at >= day, AuditLog.action == "authz.denied").count(),
                         "assessments": AuditLog.query.filter(AuditLog.created_at >= day, AuditLog.action == "assessment.run").count()},
        "health": {"audit_chain_ok": ok, "audit_bad_id": bad_id, "scanner": _scanner_status(), "sbert": _sbert_status(app_extensions)},
        "scoring": cfg,
        "recent": AuditLog.query.order_by(AuditLog.id.desc()).limit(12).all(),
    }
