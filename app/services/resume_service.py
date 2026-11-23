import hashlib
import os
import uuid
from datetime import timedelta

from flask import current_app

from ..extensions import db
from ..models.mixins import utcnow
from ..models.resume import Resume
from ..security.audit import log_event
from ..security.crypto import get_crypto
from ..security.scanner import get_scanner
from ..security.validators import safe_display_name, validate_upload


class UploadError(Exception):
    """Message is safe to show to the user."""


def _base_dir() -> str:
    base = os.path.abspath(current_app.config["UPLOAD_DIR"])
    os.makedirs(base, mode=0o700, exist_ok=True)
    return base


def safe_path(stored_name: str) -> str:
    """Resolve inside the upload directory or raise (path traversal defence)."""
    base = os.path.realpath(_base_dir())
    full = os.path.realpath(os.path.join(base, stored_name + ".bin"))
    if not full.startswith(base + os.sep):
        raise UploadError("Invalid storage path.")
    return full


def _name_aad(stored_name: str) -> bytes:
    return b"resume-name:" + stored_name.encode()


def _file_aad(stored_name: str) -> bytes:
    return b"resume-file:" + stored_name.encode()


def display_name(resume: Resume) -> str:
    try:
        return get_crypto().decrypt_field(resume.original_name_enc, _name_aad(resume.stored_name)).decode()
    except Exception:  # noqa: BLE001
        return "(unreadable name)"


def upload_resume(user, file_storage) -> Resume:
    cfg = current_app.config
    if Resume.query.filter_by(user_id=user.id).count() >= cfg["MAX_RESUMES_PER_USER"]:
        raise UploadError("You have reached the maximum number of stored resumes. Delete one first.")

    raw_name = getattr(file_storage, "filename", "") or ""
    data = file_storage.read(cfg["MAX_CONTENT_LENGTH"] + 1)

    result = validate_upload(raw_name, data, cfg["MAX_CONTENT_LENGTH"],
                             cfg["MAX_UNCOMPRESSED_MB"] * 1024 * 1024)
    if not result.ok:
        log_event("resume.upload", "rejected", user_id=user.id, detail=f"validation:{result.code}")
        raise UploadError(result.message)

    scan = get_scanner().scan(data)
    scan_status = "clean"
    if scan.status == "infected":
        log_event("resume.upload", "rejected", user_id=user.id, detail="malware_detected")
        raise UploadError("The file was rejected by the malware scanner.")
    if scan.status != "clean":
        if cfg["CLAMD_REQUIRED"]:
            log_event("resume.upload", "rejected", user_id=user.id, detail="scanner_unavailable")
            raise UploadError("The file could not be scanned right now. Please try again later.")
        scan_status = "unscanned"  # development convenience only

    stored_name = uuid.uuid4().hex
    crypto = get_crypto()
    ciphertext, nonce, wrapped = crypto.encrypt_file(data, _file_aad(stored_name))
    name_enc = crypto.encrypt_field(safe_display_name(raw_name).encode(), _name_aad(stored_name))

    path = safe_path(stored_name)
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(ciphertext)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except Exception:
        for p in (tmp, path):
            if os.path.exists(p):
                os.remove(p)
        raise

    now = utcnow()
    resume = Resume(user_id=user.id, stored_name=stored_name, original_name_enc=name_enc,
                    sha256=hashlib.sha256(data).hexdigest(), detected_mime=result.mime,
                    size_bytes=len(data), scan_status=scan_status, wrapped_dek=wrapped,
                    nonce=nonce, uploaded_at=now,
                    delete_after=now + timedelta(days=cfg["RETENTION_DAYS"]))
    try:
        db.session.add(resume)
        db.session.commit()
    except Exception:
        db.session.rollback()
        if os.path.exists(path):
            os.remove(path)
        raise
    log_event("resume.upload", "success", user_id=user.id, resource_type="resumes",
              resource_id=resume.id, detail=f"status={scan_status}")
    return resume


def read_plaintext(resume: Resume) -> bytes:
    """Decrypt a stored resume in memory (used by the parser in Phase 7)."""
    with open(safe_path(resume.stored_name), "rb") as fh:
        ciphertext = fh.read()
    return get_crypto().decrypt_file(ciphertext, resume.nonce, resume.wrapped_dek,
                                     _file_aad(resume.stored_name))


def _remove_blob(stored_name: str) -> None:
    try:
        os.remove(safe_path(stored_name))
    except FileNotFoundError:
        pass


def delete_resume(user, resume: Resume) -> None:
    """Remove ciphertext file and all rows. Deleting the wrapped key also crypto-shreds any stray copy."""
    rid, stored = resume.id, resume.stored_name
    _remove_blob(stored)
    db.session.delete(resume)
    db.session.commit()
    log_event("resume.delete", "success", user_id=user.id, resource_type="resumes", resource_id=rid)


def purge_expired() -> int:
    """Retention policy: delete resumes past their delete_after date."""
    expired = Resume.query.filter(Resume.delete_after < utcnow()).all()
    for r in expired:
        _remove_blob(r.stored_name)
        db.session.delete(r)
    db.session.commit()
    if expired:
        log_event("resume.purge", "success", detail=f"count={len(expired)}")
    return len(expired)
