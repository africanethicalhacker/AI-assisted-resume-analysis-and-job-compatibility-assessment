import io
import os

from app.models.resume import Resume
from app.services import resume_service
from tests.conftest import login, make_user, sample_docx, sample_pdf


def upload(client, data, name="cv.pdf"):
    return client.post("/resumes/", data={"file": (io.BytesIO(data), name)},
                       content_type="multipart/form-data", follow_redirects=True)


def test_upload_encrypts_at_rest_and_roundtrips(client, app):
    u = make_user("u@example.com")
    login(client, "u@example.com")
    upload(client, sample_pdf())
    r = Resume.query.one()
    on_disk = open(os.path.join(app.config["UPLOAD_DIR"], r.stored_name + ".bin"), "rb").read()
    assert b"%PDF" not in on_disk
    assert resume_service.read_plaintext(r) == sample_pdf()
    assert resume_service.display_name(r) == "cv.pdf"
    assert r.stored_name != "cv" and len(r.stored_name) == 32


def test_docx_accepted(client):
    make_user("u2@example.com")
    login(client, "u2@example.com")
    upload(client, sample_docx(), "resume.docx")
    assert Resume.query.count() == 1


def test_malware_rejected(client, scanner):
    make_user("u3@example.com")
    login(client, "u3@example.com")
    scanner.result = "infected"
    upload(client, sample_pdf())
    assert Resume.query.count() == 0


def test_scanner_down_fails_closed(client, scanner):
    make_user("u4@example.com")
    login(client, "u4@example.com")
    scanner.result = "error"
    upload(client, sample_pdf())
    assert Resume.query.count() == 0


def test_disguised_executable_rejected(client):
    make_user("u5@example.com")
    login(client, "u5@example.com")
    upload(client, b"MZ\x90\x00" + b"\0" * 100, "cv.pdf")
    assert Resume.query.count() == 0


def test_delete_removes_file_and_row(client, app):
    make_user("u6@example.com")
    login(client, "u6@example.com")
    upload(client, sample_pdf())
    r = Resume.query.one()
    path = os.path.join(app.config["UPLOAD_DIR"], r.stored_name + ".bin")
    client.post(f"/resumes/{r.id}/delete")
    assert Resume.query.count() == 0 and not os.path.exists(path)


def test_purge_expired(client, app):
    from app.extensions import db
    from app.models.mixins import utcnow
    from datetime import timedelta
    make_user("u7@example.com")
    login(client, "u7@example.com")
    upload(client, sample_pdf())
    r = Resume.query.one()
    r.delete_after = utcnow() - timedelta(days=1)
    db.session.commit()
    assert resume_service.purge_expired() == 1 and Resume.query.count() == 0
