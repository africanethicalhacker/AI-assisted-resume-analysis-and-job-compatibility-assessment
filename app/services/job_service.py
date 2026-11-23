from ..ai.jobs.analyzer import analyze_job
from ..ai.parsing.errors import ParseError
from ..ai.parsing.readers import read_document
from flask import abort

from ..extensions import db
from ..models.assessment import Assessment
from ..models.job import JobDescription, JobRequirement
from ..security.audit import log_event
from ..security.crypto import get_crypto
from ..security.sanitise import detect_injection, normalise_text
from ..security.scanner import get_scanner
from ..security.validators import validate_upload
from .taxonomy_service import get_matcher, skill_id_map

MAX_JD_CHARS = 20000


class JobError(Exception):
    """Message is safe to show to the user."""


def _aad(user_id: int) -> bytes:
    return f"job-text:{user_id}".encode()


def text_from_upload(user, file_storage, config) -> str:
    """Extract text from an uploaded PDF/DOCX job description. The file itself is not stored."""
    data = file_storage.read(config["MAX_CONTENT_LENGTH"] + 1)
    result = validate_upload(file_storage.filename or "", data, config["MAX_CONTENT_LENGTH"],
                             config["MAX_UNCOMPRESSED_MB"] * 1024 * 1024)
    if not result.ok:
        log_event("job.upload", "rejected", user_id=user.id, detail=f"validation:{result.code}")
        raise JobError(result.message)
    scan = get_scanner().scan(data)
    if scan.status == "infected" or (scan.status != "clean" and config["CLAMD_REQUIRED"]):
        log_event("job.upload", "rejected", user_id=user.id, detail=f"scan:{scan.status}")
        raise JobError("The file was rejected by the security scanner.")
    try:
        return read_document(data, result.mime).text
    except ParseError as exc:
        raise JobError(str(exc)) from exc


def create_job(user, raw_text: str, title: str = "", organization: str = "", public: bool = False, threshold: int = 60) -> JobDescription:
    text = normalise_text(raw_text, MAX_JD_CHARS)
    if len(text) < 30:
        raise JobError("The job description is too short to analyse.")
    analysis = analyze_job(text, get_matcher())
    final_title = (title or analysis["title"] or "Untitled role").strip()[:200]
    org = (organization or analysis["organization"] or "").strip()[:200] or None
    job = JobDescription(user_id=user.id, title=final_title, organization=org, is_public=public,
                         threshold=max(0, min(100, int(threshold))), status="open",
                         text_enc=get_crypto().encrypt_field(text.encode(), _aad(user.id)))
    ids = skill_id_map()
    for r in analysis["requirements"]:
        job.requirements.append(JobRequirement(
            skill_id=ids.get(r["skill_name"]) if r["skill_name"] else None,
            requirement_text=r["requirement_text"], kind=r["kind"], strength=r["strength"],
            evidence_span=r["evidence_span"]))
    db.session.add(job)
    db.session.commit()
    flags = len(detect_injection(text))
    log_event("job.post" if public else "job.create", "success", user_id=user.id, resource_type="job_descriptions",
              resource_id=job.id, detail=f"requirements={len(job.requirements)} injection_flags={flags}")
    return job


def load_text(job: JobDescription) -> str:
    return get_crypto().decrypt_field(job.text_enc, _aad(job.user_id)).decode()


def delete_job(user, job: JobDescription) -> None:
    jid = job.id
    db.session.delete(job)
    db.session.commit()
    log_event("job.delete", "success", user_id=user.id, resource_type="job_descriptions", resource_id=jid)


# ---------------- job board (postings made by administrators) ----------------
STRENGTHS = ("mandatory", "preferred", "optional")


def get_posting(job_id: int, open_only: bool = False) -> JobDescription:
    job = db.session.get(JobDescription, job_id)
    if job is None or not job.is_public or (open_only and job.status != "open"):
        abort(404)
    return job


def update_requirements(admin, job: JobDescription, strengths: dict, removals: set) -> None:
    """Let an administrator correct the automatic classification before candidates are screened against it."""
    changed = removed = 0
    for r in list(job.requirements):
        if r.kind == "responsibility":
            continue
        if r.id in removals:
            db.session.delete(r)
            removed += 1
        elif strengths.get(r.id) in STRENGTHS and strengths[r.id] != r.strength:
            r.strength = strengths[r.id]
            changed += 1
    db.session.commit()
    log_event("job.requirements_edit", "success", user_id=admin.id, resource_type="job_descriptions",
              resource_id=job.id, detail=f"changed={changed} removed={removed}")


def set_status(admin, job: JobDescription, status: str) -> None:
    if status not in ("open", "closed"):
        raise JobError("Unknown status.")
    job.status = status
    db.session.commit()
    log_event("job.status", "success", user_id=admin.id, resource_type="job_descriptions", resource_id=job.id, detail=status)


def set_threshold(admin, job: JobDescription, threshold: int) -> None:
    job.threshold = max(0, min(100, int(threshold)))
    db.session.commit()
    log_event("job.threshold", "success", user_id=admin.id, resource_type="job_descriptions", resource_id=job.id,
              detail=f"threshold={job.threshold}")


def delete_posting(admin, job: JobDescription) -> None:
    if Assessment.query.filter_by(job_id=job.id).count():
        raise JobError("Candidates have already checked this job. Close it instead of deleting it.")
    delete_job(admin, job)


def posting_stats(job: JobDescription) -> dict:
    """Aggregate figures only: no candidate identity, CV content or per-person result is exposed to administrators."""
    rows = Assessment.query.filter_by(job_id=job.id).all()
    verdicts = {"eligible": 0, "partial": 0, "not_eligible": 0}
    for a in rows:
        v = ((a.meta or {}).get("eligibility") or {}).get("verdict")
        if v in verdicts:
            verdicts[v] += 1
    n = len(rows)
    return {"checks": n, "candidates": len({a.user_id for a in rows}),
            "average_percent": round(sum(a.final_score for a in rows) / n, 1) if n else None, "verdicts": verdicts}
