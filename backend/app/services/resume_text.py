"""Resume text extraction and normalisation (DATA_PIPELINE.md section 1)."""

import io
import re

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.errors import AppError

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
        for page in reader.pages:
            text = page.extract_text() or ""
            total += len(text)
            if total > 200000:
                raise AppError("INVALID_RESUME", "The extracted resume text is too large.", 413)
            pages.append(text)
    except AppError:
        raise
    except (PdfReadError, OSError, ValueError, TypeError, KeyError) as exc:
        raise AppError(
            "INVALID_RESUME",
            "The file could not be read as a PDF.",
            415,
        ) from exc

    return normalize_text("\n".join(pages))
