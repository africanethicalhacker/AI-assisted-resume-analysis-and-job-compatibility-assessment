from flask_login import UserMixin

from ..extensions import db, login_manager
from .mixins import utcnow

ROLES = ("candidate", "administrator")


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(16), nullable=False, default="candidate")
    is_active_flag = db.Column("is_active", db.Boolean, nullable=False, default=True)
    failed_logins = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    resumes = db.relationship("Resume", back_populates="owner",
                              cascade="all, delete-orphan", passive_deletes=True)

    __table_args__ = (
        db.CheckConstraint("role IN ('candidate','administrator')", name="ck_users_role"),
    )

    @property
    def is_active(self):  # Flask-Login hook
        return bool(self.is_active_flag)

    def get_id(self):
        return str(self.id)


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None
