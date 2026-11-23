"""Tamper-evident audit log: each row stores a hash chained to the previous row.

Never pass PII (emails, names, resume text) in `detail`; use codes and IDs.
log_event() commits, so denied/failed events persist even if the caller later rolls back.
"""
import hashlib
import hmac
import re
import threading

from flask import current_app, has_request_context, request

from ..extensions import db
from ..models.audit import AuditLog
from ..models.mixins import utcnow

_lock = threading.Lock()
GENESIS = "0" * 64


def _ip_hash() -> str:
    if not has_request_context():
        return ""
    ip = request.remote_addr or ""
    key = current_app.config["SECRET_KEY"].encode()
    return hmac.new(key, ip.encode(), hashlib.sha256).hexdigest()[:32]


def _compute(prev, created_at, user_id, action, rtype, rid, ip_hash, outcome, detail) -> str:
    fields = [prev, created_at.isoformat(), str(user_id or ""), action, rtype or "",
              str(rid or ""), ip_hash, outcome, detail]
    return hashlib.sha256("|".join(fields).encode()).hexdigest()


def log_event(action, outcome, user_id=None, resource_type=None, resource_id=None, detail=""):
    detail = re.sub(r"[\x00-\x1f\x7f]", " ", detail or "")[:255]
    with _lock:
        last = AuditLog.query.order_by(AuditLog.id.desc()).first()
        prev = last.row_hash if last else GENESIS
        now = utcnow()
        iph = _ip_hash()
        row = AuditLog(user_id=user_id, action=action[:64], resource_type=resource_type,
                       resource_id=resource_id, ip_hash=iph, outcome=outcome[:16],
                       detail=detail, prev_hash=prev, created_at=now,
                       row_hash=_compute(prev, now, user_id, action[:64], resource_type,
                                         resource_id, iph, outcome[:16], detail))
        db.session.add(row)
        db.session.commit()
    return row


def verify_chain() -> tuple:
    """Return (ok, first_bad_id). Detects edited or deleted rows (not truncation of the newest rows)."""
    prev = GENESIS
    for r in AuditLog.query.order_by(AuditLog.id.asc()).yield_per(500):
        expected = _compute(prev, r.created_at, r.user_id, r.action, r.resource_type,
                            r.resource_id, r.ip_hash, r.outcome, r.detail)
        if r.prev_hash != prev or r.row_hash != expected:
            return False, r.id
        prev = r.row_hash
    return True, None
