"""Load the seed skill taxonomy into the database (idempotent): python scripts/seed_taxonomy.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.services.taxonomy_service import ensure_seed  # noqa: E402

app = create_app(os.getenv("FLASK_ENV", "development"))
with app.app_context():
    print(f"Added {ensure_seed()} skill(s).")
