from ..extensions import db
from .mixins import utcnow

MEDIUMBLOB = db.LargeBinary(length=16777215)


class Resume(db.Model):
    __tablename__ = "resumes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    stored_name = db.Column(db.String(64), unique=True, nullable=False)  # random hex, never the client name
    original_name_enc = db.Column(db.LargeBinary(length=1024), nullable=False)
    sha256 = db.Column(db.String(64), nullable=False)
    detected_mime = db.Column(db.String(100), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    scan_status = db.Column(db.String(16), nullable=False, default="clean")
    wrapped_dek = db.Column(db.LargeBinary(length=128), nullable=False)
    nonce = db.Column(db.LargeBinary(length=12), nullable=False)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    delete_after = db.Column(db.DateTime, nullable=False)

    owner = db.relationship("User", back_populates="resumes")
    profile = db.relationship("CandidateProfile", back_populates="resume", uselist=False,
                              cascade="all, delete-orphan", passive_deletes=True)

    __table_args__ = (
        db.CheckConstraint("scan_status IN ('clean','unscanned')", name="ck_resumes_scan"),
        db.Index("ix_resumes_user_uploaded", "user_id", "uploaded_at"),
        db.Index("ix_resumes_sha256", "sha256"),
        db.Index("ix_resumes_delete_after", "delete_after"),
    )
