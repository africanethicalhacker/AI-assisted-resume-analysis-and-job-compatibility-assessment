import hashlib
import math
import re

import pytest

from app import create_app
from app.extensions import db as _db
from app.ai.matching.sbert import SbertMatcher
from app.security.scanner import ScanResult


class FakeScanner:
    """Stands in for ClamAV in tests. Set .result to 'clean', 'infected' or 'error'."""
    def __init__(self):
        self.result = "clean"

    def scan(self, data):
        return ScanResult(self.result, "Test.Signature" if self.result == "infected" else "")


def fake_encoder(texts):
    """Offline stand-in for Sentence-BERT so tests never download a model."""
    out = []
    for t in texts:
        v = [0.0] * 128
        for w in re.findall(r"[a-z0-9+#]+", t.lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 128] += 1
        n = math.sqrt(sum(x * x for x in v)) or 1
        out.append([x / n for x in v])
    return out


@pytest.fixture()
def app(tmp_path):
    app = create_app("testing")
    app.config["UPLOAD_DIR"] = str(tmp_path / "uploads")
    app.config["WTF_CSRF_ENABLED"] = False
    app.instance_path = str(tmp_path / "instance")
    app.extensions["scanner"] = FakeScanner()
    app.extensions["sbert"] = SbertMatcher("fake-encoder", encoder=fake_encoder)
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def scanner(app):
    return app.extensions["scanner"]


def make_user(email, password="Correct-Horse-Battery-9", role="candidate"):
    from app.models.user import User
    from app.security.passwords import hash_password
    u = User(email=email, password_hash=hash_password(password), role=role)
    _db.session.add(u)
    _db.session.commit()
    return u


def login(client, email, password="Correct-Horse-Battery-9"):
    return client.post("/auth/login", data={"email": email, "password": password}, follow_redirects=False)


def sample_pdf() -> bytes:
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"


def sample_docx() -> bytes:
    import io
    import docx
    d = docx.Document()
    d.add_paragraph("Test resume. Python, SQL, Wireshark.")
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()
