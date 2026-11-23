from sqlalchemy import false

from ..extensions import db
from .mixins import utcnow
from .resume import MEDIUMBLOB


class JobDescription(db.Model):
    __tablename__ = "job_descriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    organization = db.Column(db.String(200), nullable=True)
    text_enc = db.Column(MEDIUMBLOB, nullable=False)
    is_public = db.Column(db.Boolean, nullable=False, default=False, server_default=false())   # posted by an administrator
    status = db.Column(db.String(10), nullable=False, default="open", server_default="open")   # open | closed
    threshold = db.Column(db.Integer, nullable=False, default=60, server_default="60")        # match % needed to be "eligible"
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    requirements = db.relationship("JobRequirement", back_populates="job",
                                   cascade="all, delete-orphan", passive_deletes=True)

    __table_args__ = (
        db.Index("ix_jobs_user_created", "user_id", "created_at"),
        db.Index("ix_jobs_public", "is_public", "status"),
        db.CheckConstraint("status IN ('open','closed')", name="ck_jobs_status"),
        db.CheckConstraint("threshold BETWEEN 0 AND 100", name="ck_jobs_threshold"),
    )


class JobRequirement(db.Model):
    __tablename__ = "job_requirements"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job_descriptions.id", ondelete="CASCADE"),
                       nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id", ondelete="SET NULL"), nullable=True)
    requirement_text = db.Column(db.String(500), nullable=False)
    kind = db.Column(db.String(24), nullable=False)
    strength = db.Column(db.String(12), nullable=False)
    evidence_span = db.Column(db.String(500), nullable=True)

    job = db.relationship("JobDescription", back_populates="requirements")

    __table_args__ = (
        db.CheckConstraint("strength IN ('mandatory','preferred','optional')", name="ck_jobreq_strength"),
        db.CheckConstraint(
            "kind IN ('skill','tool','qualification','experience','certification','responsibility','domain')",
            name="ck_jobreq_kind"),
        db.Index("ix_jobreq_job", "job_id"),
    )
