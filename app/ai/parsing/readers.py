"""Document text extraction. Inputs are untrusted; limits keep parsing bounded."""
import io
from dataclasses import dataclass

from .errors import ParseError

PDF_MIME = "application/pdf"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MAX_PDF_PAGES = 15
MIN_TEXT_CHARS = 50


@dataclass
class ReadResult:
    text: str
    hidden_chars: int = 0       # text a human cannot see (removed)
    white_text_chars: int = 0   # white-coloured text (kept, but flagged)


def read_pdf(data: bytes) -> ReadResult:
    try:
        import pymupdf as fitz  # current PyMuPDF name
    except ImportError:
        import fitz

    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:  # noqa: BLE001
        raise ParseError("The PDF could not be opened.") from exc
    hidden = white = 0
    lines = []
    try:
        if doc.needs_pass or doc.is_encrypted:
            raise ParseError("Encrypted PDFs are not supported.")
        if doc.page_count > MAX_PDF_PAGES:
            raise ParseError(f"PDFs longer than {MAX_PDF_PAGES} pages are not supported.")
        for page in doc:
            for block in page.get_text("dict").get("blocks", []):
                for line in block.get("lines", []):
                    parts = []
                    for sp in line.get("spans", []):
                        t = sp.get("text", "")
                        if not t.strip():
                            parts.append(t)
                        elif sp.get("size", 10) < 2:
                            hidden += len(t)           # microscopic text: not human-visible
                        else:
                            if sp.get("color") == 0xFFFFFF:
                                white += len(t)
                            parts.append(t)
                    lines.append("".join(parts))
                lines.append("")
    finally:
        doc.close()
    text = "\n".join(lines)
    if len(text.strip()) < MIN_TEXT_CHARS:
        raise ParseError("No readable text found. Scanned images need OCR, which is not supported.")
    return ReadResult(text, hidden, white)


def read_docx(data: bytes) -> ReadResult:
    import docx
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    try:
        document = docx.Document(io.BytesIO(data))
    except Exception as exc:  # noqa: BLE001
        raise ParseError("The DOCX file could not be opened.") from exc
    hidden = 0
    lines = []

    def paragraph_text(p):
        nonlocal hidden
        runs = p.runs
        if any(r.font.hidden for r in runs):
            visible = []
            for r in runs:
                if r.font.hidden:
                    hidden += len(r.text)
                else:
                    visible.append(r.text)
            return "".join(visible)
        return p.text

    for child in document.element.body.iterchildren():
        if child.tag.endswith("}p"):
            lines.append(paragraph_text(Paragraph(child, document)))
        elif child.tag.endswith("}tbl"):
            for row in Table(child, document).rows:
                seen, cells = set(), []
                for cell in row.cells:
                    if id(cell._tc) not in seen:       # merged cells repeat
                        seen.add(id(cell._tc))
                        cells.append(cell.text.strip())
                lines.append(" | ".join(c for c in cells if c))
    text = "\n".join(lines)
    if len(text.strip()) < MIN_TEXT_CHARS:
        raise ParseError("No readable text found in the document.")
    return ReadResult(text, hidden, 0)


def read_document(data: bytes, mime: str) -> ReadResult:
    if mime == PDF_MIME:
        return read_pdf(data)
    if mime == DOCX_MIME:
        return read_docx(data)
    raise ParseError("Unsupported document type.")
