"""Helpers shared by the API test modules."""

import csv
from pathlib import Path

from httpx import AsyncClient, Response

from app.services.job_normalize import CSV_FIELDS

PASSWORD = "correct-horse-battery"

# A resume exercising every section the deterministic parser handles.
RESUME_TEXT = """Jane Doe
jane.doe@example.com | +1 555 010 1234 | San Francisco, CA
https://github.com/janedoe

SKILLS
Python, FastAPI, PostgreSQL, Docker

EXPERIENCE
Senior Engineer | Acme Corp | Jan 2020 - Present
Built things that mattered.

EDUCATION
B.Tech in Computer Science, Example University, 2018
"""


async def auth_headers(
    client: AsyncClient, email: str = "candidate@example.com"
) -> dict[str, str]:
    """Register a user and return an Authorization header for them."""
    response = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": PASSWORD}
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['data']['token']['access_token']}"}


async def upload_resume(
    client: AsyncClient,
    headers: dict[str, str],
    data: bytes,
    *,
    filename: str = "resume.pdf",
    content_type: str = "application/pdf",
) -> Response:
    return await client.post(
        "/api/v1/resumes",
        headers=headers,
        files={"file": (filename, data, content_type)},
    )


def job_row(**overrides: object) -> dict[str, object]:
    """One dataset row with every column present and sane.

    Built from `CSV_FIELDS` so a test never has to count 26 columns by hand,
    and so a change to the source header cannot silently desync the tests.
    """
    row: dict[str, object] = {field: "" for field in CSV_FIELDS}
    row.update(
        {
            "url": "https://jobs.ashbyhq.com/acme/11111111-1111-1111-1111-111111111111",
            "title": "Senior Python Engineer",
            "company": "Acme Corp",
            "ats_type": "ashby",
            "ats_id": "11111111-1111-1111-1111-111111111111",
            "location": "London, UK",
            "employment_type": "FULL_TIME",
            "description": "We use Python, PostgreSQL and Docker. Kubernetes a plus.",
            "posted_at": "2026-01-05T10:00:00Z",
            "raw": "{}",
        }
    )
    row.update(overrides)
    return row


def write_jobs_csv(path: Path, rows: list[dict[str, object]]) -> Path:
    """Write a dataset CSV the ingester can read."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CSV_FIELDS))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})
    return path
