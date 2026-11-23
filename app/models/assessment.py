from ..extensions import db
from .mixins import utcnow


class Assessment(db.Model):
    __tablename__ = "assessments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
                           nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("job_descriptions.id", ondelete="CASCADE"),
                       nullable=False)
    final_score = db.Column(db.Float, nullable=False)
    weights_used = db.Column(db.JSON, nullable=False)
    model_version = db.Column(db.String(96), nullable=False)
    meta = db.Column(db.JSON, nullable=True)  # semantic details, integrity flags, config snapshot
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    details = db.relationship("AssessmentDetail", back_populates="assessment",
                              cascade="all, delete-orphan", passive_deletes=True)
    recommendations = db.relationship("Recommendation", back_populates="assessment",
                                      cascade="all, delete-orphan", passive_deletes=True)

    __table_args__ = (
        db.CheckConstraint("final_score BETWEEN 0 AND 100", name="ck_assessment_score"),
        db.Index("ix_assessments_user_created", "user_id", "created_at"),
    )


class AssessmentDetail(db.Model):
    __tablename__ = "assessment_details"

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey("assessments.id", ondelete="CASCADE"),
                              nullable=False)
    component = db.Column(db.String(40), nullable=False)
    score = db.Column(db.Float, nullable=False)  # 0-100
    weight = db.Column(db.Float, nullable=False)  # 0-1
    contribution = db.Column(db.Float, nullable=False)  # score * weight
    explanation = db.Column(db.JSON, nullable=True)

    assessment = db.relationship("Assessment", back_populates="details")

    __table_args__ = (
        db.UniqueConstraint("assessment_id", "component", name="uq_detail_component"),
        db.CheckConstraint("score BETWEEN 0 AND 100", name="ck_detail_score"),
        db.CheckConstraint("weight BETWEEN 0 AND 1", name="ck_detail_weight"),
    )


class Recommendation(db.Model):
    __tablename__ = "recommendations"

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey("assessments.id", ondelete="CASCADE"),
                              nullable=False)
    role_name = db.Column(db.String(100), nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    fit_score = db.Column(db.Float, nullable=False, default=0.0)
    evidence_level = db.Column(db.String(16), nullable=False, default="emerging")
    matching_skills = db.Column(db.JSON, nullable=True)
    missing_skills = db.Column(db.JSON, nullable=True)
    suggested_certs = db.Column(db.JSON, nullable=True)
    roadmap = db.Column(db.JSON, nullable=True)

    assessment = db.relationship("Assessment", back_populates="recommendations")

    __table_args__ = (db.Index("ix_reco_assessment_rank", "assessment_id", "rank"),)
