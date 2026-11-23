import io
import zipfile

from app.security.validators import safe_display_name, validate_upload

MB = 1024 * 1024
PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\n%%EOF\n"


def make_docx(extra=None, rels=None):
    import docx
    d = docx.Document()
    d.add_paragraph("hello")
    buf = io.BytesIO()
    d.save(buf)
    if not extra and not rels:
        return buf.getvalue()
    src = zipfile.ZipFile(io.BytesIO(buf.getvalue()))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for i in src.infolist():
            z.writestr(i.filename, src.read(i.filename))
        for name, content in (extra or {}).items():
            z.writestr(name, content)
        if rels:
            z.writestr("word/_rels/extra.xml.rels", rels)
    return out.getvalue()


def test_valid_pdf_and_docx():
    assert validate_upload("cv.pdf", PDF, 5 * MB).ok
    assert validate_upload("CV.DOCX", make_docx(), 5 * MB).ok


def test_empty_oversize_and_bad_extension():
    assert validate_upload("a.pdf", b"", MB).code == "empty"
    assert validate_upload("a.pdf", PDF + b"x" * (2 * MB), MB).code == "too_large"
    assert validate_upload("a.exe", PDF, MB).code == "bad_extension"
    assert validate_upload("noext", PDF, MB).code == "bad_extension"


def test_magic_mismatch_both_directions():
    assert validate_upload("a.pdf", make_docx(), 5 * MB).code == "magic_mismatch"
    assert validate_upload("a.docx", PDF, 5 * MB).code == "magic_mismatch"
    assert validate_upload("a.pdf", b"MZ\x90\x00 not a pdf", MB).code == "magic_mismatch"


def test_double_extension_uses_last():
    assert validate_upload("cv.pdf.exe", PDF, MB).code == "bad_extension"


def test_pdf_active_content_and_encryption_and_truncation():
    js = b"%PDF-1.4\n1 0 obj<</S/JavaScript/JS(app.alert(1))>>endobj\n%%EOF\n"
    assert validate_upload("a.pdf", js, MB).code == "pdf_active_content"
    enc = b"%PDF-1.4\ntrailer<</Encrypt 5 0 R>>\n%%EOF\n"
    assert validate_upload("a.pdf", enc, MB).code == "pdf_encrypted"
    assert validate_upload("a.pdf", b"%PDF-1.4\nno end marker", MB).code == "pdf_truncated"


def test_docx_macro_and_embedded_rejected():
    assert validate_upload("a.docx", make_docx({"word/vbaProject.bin": b"x"}), 5 * MB).code == "docx_active_content"
    assert validate_upload("a.docx", make_docx({"word/embeddings/o.bin": b"x"}), 5 * MB).code == "docx_active_content"


def test_docx_remote_template_rejected_but_hyperlink_allowed():
    bad = ('<Relationships><Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
           'relationships/attachedTemplate" Target="http://evil.example/t.dotm" TargetMode="External"/></Relationships>')
    ok = ('<Relationships><Relationship Id="r2" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
          'relationships/hyperlink" Target="https://github.com/x" TargetMode="External"/></Relationships>')
    assert validate_upload("a.docx", make_docx(rels=bad), 5 * MB).code == "docx_remote_content"
    assert validate_upload("a.docx", make_docx(rels=ok), 5 * MB).ok


def test_docx_path_traversal_and_bomb_and_structure():
    assert validate_upload("a.docx", make_docx({"../evil.txt": b"x"}), 5 * MB).code == "docx_path_traversal"
    bomb = make_docx({"word/big.bin": b"\0" * (60 * MB)})
    assert validate_upload("a.docx", bomb, 5 * MB, max_uncompressed=50 * MB).code in {"docx_zip_bomb"}
    notdocx = io.BytesIO()
    with zipfile.ZipFile(notdocx, "w") as z:
        z.writestr("hello.txt", "hi")
    assert validate_upload("a.docx", notdocx.getvalue(), MB).code == "docx_structure"
    assert validate_upload("a.docx", b"PK\x03\x04garbage", MB).code == "docx_not_zip"


def test_safe_display_name():
    assert safe_display_name("../../etc/passwd") == "passwd"
    assert safe_display_name("C:\\Users\\me\\<script>.pdf") == "_script_.pdf"
    assert safe_display_name("") == "resume"
    assert len(safe_display_name("a" * 500 + ".pdf")) <= 100
