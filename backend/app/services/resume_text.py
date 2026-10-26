"""Resume text extraction and normalisation (DATA_PIPELINE.md section 1)."""

import io
import re
import math
from urllib.parse import urlparse

import pdfplumber

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.errors import AppError
from app.services.resume_parser import _section_for
from app.services.resume_layout import ordered_text

PDF_MIME_TYPE = "application/pdf"

_HORIZONTAL_WHITESPACE = re.compile(r"[ \t   ]+")
_EXCESS_BLANK_LINES = re.compile(r"\n{3,}")


def normalize_text(text: str) -> str:
    """Collapse the whitespace that PDF extraction introduces.

    Every line gets stripped and runs of blank lines become a single separator,
    because the section detector keys off line position.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _HORIZONTAL_WHITESPACE.sub(" ", text)
    lines = (line.strip() for line in text.split("\n"))
    return _EXCESS_BLANK_LINES.sub("\n\n", "\n".join(lines)).strip()


def extract_text(data: bytes, mime_type: str) -> str:
    """Return the normalised text of a PDF, or raise `INVALID_RESUME`.

    A file we cannot parse is rejected at the boundary rather than stored and
    left to fail somewhere less obvious.
    """
    if mime_type != PDF_MIME_TYPE:
        raise AppError(
            "INVALID_RESUME",
            "Only PDF resumes are supported.",
            415,
        )

    try:
        reader = PdfReader(io.BytesIO(data))
        if len(reader.pages) > 30:
            raise AppError("INVALID_RESUME", "Resumes must contain at most 30 pages.", 413)
        if reader.is_encrypted and not reader.decrypt(""):
            raise AppError(
                "INVALID_RESUME",
                "The PDF is password-protected.",
                415,
            )
        pages = []
        total = 0
        # Design-tool PDFs may draw headings after their bodies. PDFMiner's
        # positional layout restores visual order, unlike content-stream order.
        links, header_lines = [], set()
        with pdfplumber.open(io.BytesIO(data), password="") as document:
            for index, page in enumerate(reader.pages):
                positioned = document.pages[index]
                layout = positioned.crop(positioned.bbox).extract_text(layout=True, x_tolerance=1) if 0 < positioned.width <= 4000 and 0 < positioned.height <= 4000 else None
                text = layout or page.extract_text() or ""
                extracted_length = len(text)
                total += extracted_length
                if total > 200000:
                    raise AppError("INVALID_RESUME", "The extracted resume text is too large.", 413)
                if layout and hasattr(positioned, "extract_words"):
                    text = ordered_text(positioned, text)
                if not text.strip():
                    raise AppError("INVALID_RESUME", "Every resume page must contain searchable text. Scanned pages need OCR; AI assistance cannot read images.", 415)
                if index == 0:
                    for line in normalize_text(text).splitlines()[:12]:
                        if _section_for(line):
                            break
                        if line.strip():
                            header_lines.add(line.strip())
                else:
                    # Exact repeated header lines only; do not drop page-two
                    # sections or invent a continuation from unrelated text.
                    lines = text.splitlines()
                    for row in range(min(4, len(lines))):
                        if lines[row].strip() in header_lines:
                            lines[row] = ""
                    text = "\n".join(lines)
                total += len(text) - extracted_length
                if total > 200000:
                    raise AppError("INVALID_RESUME", "The extracted resume text is too large.", 413)
                pages.append(text)
                section_top = min((line["top"] for line in positioned.extract_text_lines()
                    if _section_for(line["text"].strip())), default=positioned.height * 0.25) if index == 0 else 0
                for reference in page.get("/Annots", []) if index == 0 and not page.get("/Rotate", 0) else []:
                    annotation = reference.get_object()
                    if not hasattr(annotation, "get"):
                        continue
                    rect = annotation.get("/Rect", [])
                    if len(rect) != 4:
                        continue
                    x0, y0, x1, y1 = (float(v) for v in rect)
                    # Only first-page contact/header annotations. Employer or
                    # project body links must never become a personal website.
                    box = page.mediabox
                    if not all(math.isfinite(v) for v in (x0,y0,x1,y1)) or not (
                        float(box.left) <= x0 < x1 <= float(box.right)
                        and float(box.bottom) + float(box.height) * 0.75 <= y0 < y1 <= float(box.top)
                        and float(box.top) - y0 < section_top):
                        continue
                    action = annotation.get("/A")
                    action = action.get_object() if hasattr(action, "get_object") else action
                    if not hasattr(action, "get"):
                        continue
                    uri = str(action.get("/URI", ""))
                    parts = urlparse(uri)
                    if parts.scheme in {"http", "https"} and parts.hostname and not parts.username and not parts.password and len(uri) <= 2048 and uri not in links and len(links) < 64:
                        links.append(uri)
        # Copy embedded HTTP links, never construct URLs from visible handles.
        total += sum(len(link) + 1 for link in links)
        if total > 200000:
            raise AppError("INVALID_RESUME", "The extracted resume text is too large.", 413)
    except AppError:
        raise
    except (PdfReadError, OSError, ValueError, TypeError, KeyError) as exc:
        raise AppError(
            "INVALID_RESUME",
            "The file could not be read as a PDF.",
            415,
        ) from exc

    result = normalize_text("\n".join(pages))
    if not result.strip():
        raise AppError("INVALID_RESUME", "The resume must contain searchable text.", 415)
    if links:
        # Keep copied contact links in the header, not in a trailing skills or
        # project section. Preserve the first name/title line and all body text.
        first, separator, rest = result.partition("\n")
        result = normalize_text(first + "\n" + "\n".join(links) + separator + rest)
    return result
