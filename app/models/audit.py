from ..extensions import db
from .mixins import utcnow

BigId = db.BigInteger().with_variant(db.Integer, "sqlite")


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(BigId, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=True)  # no FK: audit rows must never change when an account is erased
    action = db.Column(db.String(64), nullable=False)
    resource_type = db.Column(db.String(32), nullable=True)
    resource_id = db.Column(db.Integer, nullable=True)
    ip_hash = db.Column(db.String(32), nullable=False, default="")
    outcome = db.Column(db.String(16), nullable=False)
    detail = db.Column(db.String(255), nullable=False, default="")
    prev_hash = db.Column(db.String(64), nullable=False)
    row_hash = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    __table_args__ = (
        db.Index("ix_audit_action", "action"),
        db.Index("ix_audit_user_created", "user_id", "created_at"),
        db.Index("ix_audit_created", "created_at"),
    )
