"""Read the existing discovery catalog, not companies on a page of jobs."""
import json
from functools import lru_cache
from pathlib import Path

from pydantic import ValidationError

from app.core.errors import AppError
from app.schemas.job import CompanyData, CompanySuggestions


@lru_cache(maxsize=1)
def _read(path: str, modified: int, size: int) -> tuple[CompanyData, ...]:
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    return tuple(CompanyData.model_validate(row) for row in rows)


def search(path: Path, query: str, limit: int) -> CompanySuggestions:
    try:
        stat = path.stat()
        companies = _read(str(path.resolve()), stat.st_mtime_ns, stat.st_size)
    except (OSError, ValueError, TypeError, ValidationError) as exc:
        raise AppError("COMPANY_CATALOG_UNAVAILABLE", "Company suggestions are temporarily unavailable.", 503) from exc
    term = query.strip().casefold()
    matches = [row for row in companies if term in row.company.casefold() or term in row.slug.casefold()]
    matches.sort(key=lambda row: (not row.company.casefold().startswith(term), row.company.casefold(), row.slug))
    return CompanySuggestions(companies=matches[:limit], total=len(matches))
