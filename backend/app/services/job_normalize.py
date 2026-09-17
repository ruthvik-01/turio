"""Normalise one Stapply dataset row (DATASET.md sections 4 and 5).

Every field is optional except the three the `jobs` table declares NOT NULL
(`title`, `company`, `job_url`). An absent optional field becomes `None` rather
than an empty string or a guess — DATASET.md section 4 is explicit that a
missing field is recorded, not assumed.

Two columns the schema document describes are absent from the CSV itself
(`global_id` and a structured `experience`), so `external_id` is derived from
the same inputs `global_id` is defined from, and `experience_requirement`
stays null rather than being parsed out of prose.
"""

import hashlib
import base64
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from app.services.skills import extract_skills
from app.services.job_metadata import deadline, logo_url, source_metadata

# The CSV header, in order. Anything not in here is left in raw_payload.
CSV_FIELDS: tuple[str, ...] = (
    "url",
    "title",
    "company",
    "ats_type",
    "ats_id",
    "location",
    "country_iso",
    "region",
    "language",
    "lat",
    "lon",
    "is_remote",
    "salary_min",
    "salary_max",
    "salary_currency",
    "salary_period",
    "salary_summary",
    "employment_type",
    "department",
    "team",
    "description",
    "posted_at",
    "requisition_id",
    "apply_url",
    "commitment",
    "raw",
)

# Checksummed over exactly these, so "same hash" means "same stored row".
_HASHED_FIELDS = (
    "title",
    "company",
    "description",
    "location",
    "job_url",
    "application_url",
    "ats",
    "required_skills",
    "required_education",
    "experience_requirement",
    "raw_payload",
    "application_deadline",
    "company_logo_url",
)

_HORIZONTAL_WHITESPACE = re.compile(r"[ \t ]+")
_HTML_TAG = re.compile(r"<[^>]+>")


def clean(value: Any) -> str | None:
    """Trim, strip residual markup, and treat blank as absent."""
    if value is None:
        return None
    text = _HTML_TAG.sub(" ", str(value).replace("\x00", " "))
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _HORIZONTAL_WHITESPACE.sub(" ", text)
    text = text.strip()
    return text or None


def build_external_id(row: Mapping[str, Any]) -> str | None:
    """A key that is stable across re-imports.

    Defined the way the source's own `global_id` is - `ats_type:ats_id` - with a
    URL digest as the fallback, because a random id here would break
    re-ingestion idempotence. Returns None when the row carries nothing stable
    to identify it by.
    """
    ats_type = clean(row.get("ats_type"))
    ats_id = clean(row.get("ats_id"))
    if ats_type and ats_id:
        return f"{ats_type}:{ats_id}"

    url = clean(row.get("url"))
    if url:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
    return None


@dataclass(frozen=True)
class NormalizedJob:
    external_id: str
    title: str
    company: str
    description: str | None
    location: str | None
    job_url: str
    application_url: str | None
    ats: str | None
    required_skills: list[str]
    required_education: list[str] | None
    experience_requirement: dict[str, Any] | None
    raw_payload: dict[str, Any]
    content_hash: str
    application_deadline: datetime | None = None
    company_logo_url: str | None = None


def content_hash(job: NormalizedJob) -> str:
    payload = {name: getattr(job, name) for name in _HASHED_FIELDS}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normalize_row(row: Mapping[str, Any]) -> NormalizedJob | None:
    """Normalise one CSV row, or return None if it cannot be a job record."""
    external_id = build_external_id(row)
    title = clean(row.get("title"))
    company = clean(row.get("company"))
    job_url = clean(row.get("url"))

    # Matches the NOT NULL columns on `jobs`; a row lacking one cannot be
    # stored, and is counted rather than silently dropped.
    if external_id is None or title is None or company is None or job_url is None:
        return None

    description = clean(row.get("description"))
    required_skills = extract_skills(f"{title}\n{description or ''}")

    raw_payload = {}
    for field in row:
        if field is None:
            continue
        value = row[field]
        # CSV values are strings/None. A tagged object preserves exceptional
        # bytes without PostgreSQL's text/JSONB NUL restriction or ambiguity
        # with an original literal "\\u0000" sequence.
        raw_payload[field] = (
            {"encoding": "utf8-base64", "data": base64.b64encode(value.encode("utf-8")).decode("ascii")}
            if isinstance(value, str) and "\x00" in value else value
        )
    metadata = source_metadata(row)
    job = NormalizedJob(
        external_id=external_id,
        title=title,
        company=company,
        description=description,
        location=clean(row.get("location")),
        job_url=job_url,
        application_url=clean(row.get("apply_url")),
        ats=clean(row.get("ats_type")),
        required_skills=required_skills,
        # Not derivable from this source: the CSV carries no education field,
        # and inferring a requirement from prose would be inventing one.
        required_education=None,
        # Likewise: the CSV has no structured years field. The schema document
        # notes that prose like "3+ years" stays null even in the source model.
        experience_requirement=None,
        raw_payload=raw_payload,
        content_hash="",
        application_deadline=deadline(metadata.get("application_deadline") or metadata.get("validThrough")),
        company_logo_url=logo_url(metadata.get("company_logo_url") or metadata.get("logo_url")),
    )
    return NormalizedJob(**{**job.__dict__, "content_hash": content_hash(job)})
