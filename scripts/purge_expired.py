"""Retention job: python scripts/purge_expired.py  (run daily via cron or a systemd timer)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.services.resume_service import purge_expired  # noqa: E402

app = create_app(os.getenv("FLASK_ENV", "development"))
with app.app_context():
    print(f"Purged {purge_expired()} expired resume(s).")
