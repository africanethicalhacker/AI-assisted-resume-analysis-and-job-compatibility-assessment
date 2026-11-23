"""Create an administrator account: python scripts/create_admin.py"""
import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.user import User  # noqa: E402
from app.security import passwords  # noqa: E402
from app.services.auth_service import normalise_email  # noqa: E402

app = create_app(os.getenv("FLASK_ENV", "development"))
with app.app_context():
    email = normalise_email(input("Admin email: "))
    pw = getpass.getpass("Password (12+ chars): ")
    if pw != getpass.getpass("Confirm password: "):
        sys.exit("Passwords do not match.")
    errors = passwords.validate_password(pw, email)
    if errors:
        sys.exit(" ".join(errors))
    if User.query.filter_by(email=email).first():
        sys.exit("A user with that email already exists.")
    db.session.add(User(email=email, password_hash=passwords.hash_password(pw), role="administrator"))
    db.session.commit()
    print("Administrator created.")
