"""Upload validation. The client filename and Content-Type are never trusted.

Checks, in order: size, extension, magic bytes, structure, dangerous content.
Limitation (documented in the report): byte-level PDF token scanning cannot see
inside compressed object streams; deeper PDF inspection happens at parse time.
"""
import io
import os
import re
import zipfile
from dataclasses import dataclass

PDF_MIME = "application/pdf"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
ALLOWED = {"pdf": PDF_MIME, "docx": DOCX_MIME}

_PDF_DANGEROUS = re.compile(rb"/(JavaScript|JS|Launch|EmbeddedFile|RichMedia|XFA|Encrypt)(?![A-Za-z0-9])")
_REL_TAG = re.compile(rb"<Relationship\b[^>]*>", re.IGNORECASE)
_BAD_REL_TYPES = (b"attachedtemplate", b"oleobject", b"subdocument", b"frame", b"externalLink".lower())


@dataclass
class ValidationResult:
    ok: bool
    code: str = "ok"          # short machine code, safe to log
    message: str = ""         # user-safe message
    mime: str = ""
    kind: str = ""


def _fail(code: str, message: str) -> ValidationResult:
    return ValidationResult(False, code, message)


def safe_display_name(raw: str) -> str:
    """Sanitised name for display only (stored encrypted); never used for paths."""
    name = os.path.basename((raw or "").replace("\\", "/"))
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip(" .")
    return name[:100] or "resume"


def _check_pdf(data: bytes) -> ValidationResult:
    if b"%%EOF" not in data[-2048:]:
        return _fail("pdf_truncated", "The PDF appears to be damaged or incomplete.")
    hit = _PDF_DANGEROUS.search(data)
    if hit:
        token = hit.group(1)
        if token == b"Encrypt":
            return _fail("pdf_encrypted", "Encrypted or password-protected PDFs are not accepted.")
        return _fail("pdf_active_content", "PDFs containing scripts or embedded content are not accepted.")
    return ValidationResult(True, mime=PDF_MIME, kind="pdf")


def _check_docx(data: bytes, max_uncompressed: int) -> ValidationResult:
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        return _fail("docx_not_zip", "The DOCX file is damaged.")
    with zf:
        infos = zf.infolist()
        if len(infos) > 2000:
            return _fail("docx_too_many_entries", "The document structure is not acceptable.")
        names = [i.filename for i in infos]
        total = 0
        for i in infos:
            n = i.filename
            if n.startswith(("/", "\\")) or ".." in n.replace("\\", "/").split("/") or ":" in n:
                return _fail("docx_path_traversal", "The document structure is not acceptable.")
            total += i.file_size
            if i.compress_size > 0 and i.file_size / i.compress_size > 200 and i.file_size > 1_000_000:
                return _fail("docx_zip_bomb", "The document structure is not acceptable.")
            if i.flag_bits & 0x1:
                return _fail("docx_encrypted", "Encrypted documents are not accepted.")
        if total > max_uncompressed:
            return _fail("docx_zip_bomb", "The document is too large when expanded.")
        if "[Content_Types].xml" not in names or "word/document.xml" not in names:
            return _fail("docx_structure", "This is not a valid Word (.docx) document.")
        lowered = [n.lower() for n in names]
        if any(n.endswith("vbaproject.bin") or "/activex/" in n or "/embeddings/" in n for n in lowered):
            return _fail("docx_active_content", "Documents with macros or embedded objects are not accepted.")
        for n in names:
            if n.endswith(".rels"):
                try:
                    xml = zf.read(n)
                except Exception:  # noqa: BLE001
                    return _fail("docx_structure", "The document structure is not acceptable.")
                for tag in _REL_TAG.findall(xml):
                    low = tag.lower()
                    if b'targetmode="external"' in low and any(t in low for t in _BAD_REL_TYPES):
                        return _fail("docx_remote_content",
                                     "Documents that reference external templates or objects are not accepted.")
    return ValidationResult(True, mime=DOCX_MIME, kind="docx")


def validate_upload(filename: str, data: bytes, max_bytes: int,
                    max_uncompressed: int = 50 * 1024 * 1024) -> ValidationResult:
    if not data:
        return _fail("empty", "The file is empty.")
    if len(data) > max_bytes:
        return _fail("too_large", f"The file exceeds the {max_bytes // (1024 * 1024)} MB limit.")
    ext = os.path.splitext((filename or "").replace("\\", "/"))[1].lower().lstrip(".")
    if ext not in ALLOWED:
        return _fail("bad_extension", "Only PDF and DOCX files are accepted.")
    is_pdf = data[:5] == b"%PDF-"
    is_zip = data[:4] == b"PK\x03\x04"
    if ext == "pdf" and not is_pdf:
        return _fail("magic_mismatch", "The file content does not match its extension.")
    if ext == "docx" and not is_zip:
        return _fail("magic_mismatch", "The file content does not match its extension.")
    return _check_pdf(data) if ext == "pdf" else _check_docx(data, max_uncompressed)
