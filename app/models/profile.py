from ..extensions import db
from .mixins import utcnow
from .resume import MEDIUMBLOB


class CandidateProfile(db.Model):
    __tablename__ = "candidate_profiles"

    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id", ondelete="CASCADE"),
                          unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    profile_enc = db.Column(MEDIUMBLOB, nullable=False)  # AES-GCM encrypted JSON with PII
    parser_version = db.Column(db.String(32), nullable=False)
    resume_quality_score = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    resume = db.relationship("Resume", back_populates="profile")
    skills = db.relationship("CandidateSkill", back_populates="profile",
                             cascade="all, delete-orphan", passive_deletes=True)

    __table_args__ = (
        db.CheckConstraint("resume_quality_score IS NULL OR (resume_quality_score BETWEEN 0 AND 100)",
                           name="ck_profiles_quality"),
        db.Index("ix_profiles_user", "user_id"),
    )


class Skill(db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    aliases = db.Column(db.Text, nullable=True)  # pipe-separated alternative spellings
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (db.Index("ix_skills_category", "category"),)


class CandidateSkill(db.Model):
    __tablename__ = "candidate_skills"

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
                           nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    source_type = db.Column(db.String(16), nullable=False)  # explicit | inferred
    confidence = db.Column(db.Float, nullable=False, default=1.0)
    evidence_enc = db.Column(db.LargeBinary(length=4096), nullable=True)

    profile = db.relationship("CandidateProfile", back_populates="skills")
    skill = db.relationship("Skill")

    __table_args__ = (
        db.UniqueConstraint("profile_id", "skill_id", name="uq_candidate_skill"),
        db.CheckConstraint("source_type IN ('explicit','inferred')", name="ck_cskill_source"),
        db.CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_cskill_conf"),
    )
