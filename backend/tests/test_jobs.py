"""Phase 3 job ingestion (PHASE_PLAN.md Phase 3, DATASET.md sections 4-5)."""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.repositories import jobs as job_repo
from app.services.job_ingestion import ingest_dataset
from support import auth_headers, job_row, write_jobs_csv


async def _snapshot(session: AsyncSession) -> list[tuple[Any, ...]]:
    """Every stored job's full detail, for comparing one run against another."""
    result = await session.execute(select(Job).order_by(Job.external_id))
    return [
        (
            job.id,
            job.external_id,
            job.title,
            job.company,
            job.location,
            job.content_hash,
            job.fetched_at,
            job.required_skills,
        )
        for job in result.scalars().all()
    ]


# --- normalisation --------------------------------------------------------


async def test_ingestion_stores_normalised_jobs(
    session: AsyncSession, tmp_path: Path
) -> None:
    path = write_jobs_csv(tmp_path / "jobs.csv", [job_row()])

    summary = await ingest_dataset(session, path=str(path))

    assert summary.rows_read == 1
    assert summary.inserted == 1
    assert summary.rejected == 0

    jobs, total = await job_repo.list_jobs(session)
    assert total == 1
    job = jobs[0]
    assert job.external_id == "ashby:11111111-1111-1111-1111-111111111111"
    assert job.title == "Senior Python Engineer"
    assert job.company == "Acme Corp"
    assert job.ats == "ashby"
    assert job.location == "London, UK"
    # Skills named verbatim in the description, canonicalised.
    assert job.required_skills == ["docker", "kubernetes", "postgresql", "python"]
    # Not derivable from this source, and not invented.
    assert job.required_education is None
    assert job.experience_requirement is None
    # Everything the normalised columns do not carry is still kept.
    assert job.raw_payload["employment_type"] == "FULL_TIME"


async def test_missing_optional_fields_become_null_not_guesses(
    session: AsyncSession, tmp_path: Path
) -> None:
    """PHASE_PLAN.md Phase 3 exit checklist item (b)."""
    # Title carries no lexicon skill either, so a non-empty list here would
    # mean something was invented rather than found.
    path = write_jobs_csv(
        tmp_path / "jobs.csv",
        [job_row(title="Barista", location="", description="", apply_url="", raw="")],
    )

    summary = await ingest_dataset(session, path=str(path))

    # The row is kept, not skipped, for lacking optional fields.
    assert summary.inserted == 1
    assert summary.rejected == 0

    jobs, _ = await job_repo.list_jobs(session)
    job = jobs[0]
    assert job.location is None
    assert job.description is None
    assert job.application_url is None
    assert job.required_skills == []


async def test_markup_and_whitespace_are_cleaned(session: AsyncSession, tmp_path: Path) -> None:
    path = write_jobs_csv(
        tmp_path / "jobs.csv",
        [job_row(description="<p>Build   things</p>\n\n<b>with Python</b>")],
    )

    await ingest_dataset(session, path=str(path))

    jobs, _ = await job_repo.list_jobs(session)
    assert "<" not in (jobs[0].description or "")
    assert "Build things" in (jobs[0].description or "")


async def test_rows_without_a_required_field_are_counted_not_silently_dropped(
    session: AsyncSession, tmp_path: Path
) -> None:
    path = write_jobs_csv(
        tmp_path / "jobs.csv",
        [
            job_row(),
            job_row(ats_id="2", title=""),  # no title -> cannot be a job record
            job_row(ats_id="3", url=""),  # no url and no usable identity
        ],
    )

    summary = await ingest_dataset(session, path=str(path))

    assert summary.rows_read == 3
    assert summary.inserted == 1
    assert summary.rejected == 2
    assert await job_repo.count(session) == 1


async def test_row_without_an_ats_id_is_identified_by_its_url(
    session: AsyncSession, tmp_path: Path
) -> None:
    """Identity must stay stable, or re-ingestion would duplicate the row."""
    path = write_jobs_csv(tmp_path / "jobs.csv", [job_row(ats_type="", ats_id="")])

    first = await ingest_dataset(session, path=str(path))
    second = await ingest_dataset(session, path=str(path))

    assert first.inserted == 1
    assert second.inserted == 0
    assert second.unchanged == 1
    assert await job_repo.count(session) == 1


# --- idempotence and reprocessing -----------------------------------------


async def test_reingesting_unchanged_data_changes_nothing(
    session: AsyncSession, tmp_path: Path
) -> None:
    """PHASE_PLAN.md Phase 3 exit checklist item (a).

    Compares every stored column before and after, not just the row count, so a
    silent UPDATE that happens to preserve the count is still caught.
    """
    path = write_jobs_csv(tmp_path / "jobs.csv", [job_row(), job_row(ats_id="2", title="Other")])

    first = await ingest_dataset(session, path=str(path))
    assert first.inserted == 2
    before = await _snapshot(session)

    second = await ingest_dataset(session, path=str(path))

    assert second.inserted == 0
    assert second.updated == 0
    assert second.unchanged == 2
    assert await _snapshot(session) == before


async def test_changed_content_is_reprocessed_in_place(
    session: AsyncSession, tmp_path: Path
) -> None:
    """PHASE_PLAN.md Phase 3 exit checklist item (c)."""
    path = write_jobs_csv(tmp_path / "jobs.csv", [job_row()])
    await ingest_dataset(session, path=str(path))

    write_jobs_csv(path, [job_row(title="Staff Python Engineer")])
    summary = await ingest_dataset(session, path=str(path))

    assert summary.updated == 1
    assert summary.inserted == 0
    # Updated, not duplicated.
    assert await job_repo.count(session) == 1
    jobs, _ = await job_repo.list_jobs(session)
    assert jobs[0].title == "Staff Python Engineer"


async def test_unchanged_rows_keep_their_original_fetched_at(
    session: AsyncSession, tmp_path: Path
) -> None:
    path = write_jobs_csv(tmp_path / "jobs.csv", [job_row()])
    await ingest_dataset(session, path=str(path))
    stored = (await _snapshot(session))[0][6]
    assert isinstance(stored, datetime)

    await ingest_dataset(session, path=str(path))

    assert (await _snapshot(session))[0][6] == stored


async def test_duplicate_rows_within_one_file_produce_one_row(
    session: AsyncSession, tmp_path: Path
) -> None:
    """DATASET.md section 5: remove duplicate records."""
    path = write_jobs_csv(tmp_path / "jobs.csv", [job_row(), job_row()])

    summary = await ingest_dataset(session, path=str(path))

    assert summary.rows_read == 2
    assert await job_repo.count(session) == 1


async def test_duplicate_rows_across_batches_produce_one_row(
    session: AsyncSession, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "job_ingest_batch_size", 1)
    path = write_jobs_csv(tmp_path / "jobs.csv", [job_row(), job_row()])

    summary = await ingest_dataset(session, path=str(path))

    assert summary.rows_read == 2
    assert summary.inserted == 1
    assert summary.updated == 0
    assert summary.unchanged == 1
    assert await job_repo.count(session) == 1
    before = await _snapshot(session)
    repeated = await ingest_dataset(session, path=str(path))
    assert repeated.inserted == repeated.updated == 0
    assert repeated.unchanged == 2
    assert await _snapshot(session) == before


@pytest.mark.parametrize("batch_size", [1, 2, 1000])
@pytest.mark.parametrize("preexisting", [False, True])
async def test_changed_duplicates_across_batches_keep_last_content(
    session: AsyncSession,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    batch_size: int,
    preexisting: bool,
) -> None:
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "job_ingest_batch_size", batch_size)
    if preexisting:
        seed = write_jobs_csv(tmp_path / "seed.csv", [job_row()])
        await ingest_dataset(session, path=str(seed))
    path = write_jobs_csv(
        tmp_path / "jobs.csv",
        [job_row(), job_row(title="Staff Python Engineer"), job_row()],
    )

    summary = await ingest_dataset(session, path=str(path))

    jobs, total = await job_repo.list_jobs(session)
    assert total == 1
    assert jobs[0].title == "Senior Python Engineer"
    assert summary.inserted == (0 if preexisting else 1)
    assert summary.updated == 2
    assert summary.unchanged == (1 if preexisting else 0)


async def test_missing_dataset_file_is_reported_not_crashed(session: AsyncSession) -> None:
    from app.core.errors import AppError

    try:
        await ingest_dataset(session, path="does/not/exist.csv")
    except AppError as exc:
        assert exc.code == "JOB_SOURCE_UNAVAILABLE"
        assert exc.http_status == 503
    else:  # pragma: no cover - the call above must raise
        raise AssertionError("expected JOB_SOURCE_UNAVAILABLE")


# --- routes ---------------------------------------------------------------


async def test_job_routes_require_authentication(client: AsyncClient) -> None:
    read = await client.get("/api/v1/jobs")
    detail = await client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000")
    refresh = await client.post("/api/v1/jobs/refresh")

    for response in (read, detail, refresh):
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_job_list_filters_and_paginates(
    client: AsyncClient, session: AsyncSession, tmp_path: Path
) -> None:
    write_jobs_csv(
        tmp_path / "jobs.csv",
        [
            job_row(),
            job_row(ats_id="2", title="Data Analyst", company="Globex", location="Berlin, DE"),
            job_row(ats_id="3", title="Platform Engineer", company="Acme Corp"),
        ],
    )
    await ingest_dataset(session, path=str(tmp_path / "jobs.csv"))
    headers = await auth_headers(client)

    everything = await client.get("/api/v1/jobs", headers=headers)
    assert everything.status_code == 200
    assert everything.json()["data"]["total"] == 3

    by_company = await client.get("/api/v1/jobs?company=Acme Corp", headers=headers)
    assert by_company.json()["data"]["total"] == 2

    by_query = await client.get("/api/v1/jobs?q=analyst", headers=headers)
    assert by_query.json()["data"]["total"] == 1
    assert by_query.json()["data"]["jobs"][0]["title"] == "Data Analyst"

    by_location = await client.get("/api/v1/jobs?location=berlin", headers=headers)
    assert by_location.json()["data"]["total"] == 1

    by_ats = await client.get("/api/v1/jobs?ats=ashby", headers=headers)
    assert by_ats.json()["data"]["total"] == 3

    page = await client.get("/api/v1/jobs?limit=2&offset=0", headers=headers)
    assert len(page.json()["data"]["jobs"]) == 2
    assert page.json()["data"]["total"] == 3


async def test_unknown_job_is_404_not_500(client: AsyncClient) -> None:
    headers = await auth_headers(client)

    response = await client.get(
        "/api/v1/jobs/00000000-0000-0000-0000-000000000000", headers=headers
    )

    assert response.status_code == 404
    body = response.json()
    assert body["data"] is None
    assert body["error"]["code"] == "NOT_FOUND"


async def test_job_detail_returns_the_stored_job(
    client: AsyncClient, session: AsyncSession, tmp_path: Path
) -> None:
    write_jobs_csv(tmp_path / "jobs.csv", [job_row()])
    await ingest_dataset(session, path=str(tmp_path / "jobs.csv"))
    headers = await auth_headers(client)

    listing = await client.get("/api/v1/jobs", headers=headers)
    job_id = listing.json()["data"]["jobs"][0]["id"]

    detail = await client.get(f"/api/v1/jobs/{job_id}", headers=headers)

    assert detail.status_code == 200
    assert detail.json()["data"]["external_id"].startswith("ashby:")


# --- Phase 2 compatibility ------------------------------------------------


def test_nul_text_is_normalized_and_raw_provenance_is_reversible():
    import base64
    from app.services.job_normalize import normalize_row

    original = "Python\x00and PostgreSQL; literal \\u0000 remains literal."
    normalized = normalize_row(job_row(description=original))
    assert "\x00" not in normalized.description
    assert "Python and PostgreSQL" in normalized.description
    raw = normalized.raw_payload["description"]
    assert raw["encoding"] == "utf8-base64"
    assert base64.b64decode(raw["data"]).decode("utf-8") == original
    assert normalized.content_hash == normalize_row(job_row(description=original)).content_hash


async def test_ingestion_does_not_touch_profile_or_resume_tables(
    client: AsyncClient, session: AsyncSession, tmp_path: Path
) -> None:
    """Phase 3 compatibility check: jobs are a separate concern from profiles."""
    from sqlalchemy import func

    from app.models.profile import Profile
    from app.models.resume import Resume

    headers = await auth_headers(client)
    profile_id = (await client.get("/api/v1/profiles/me", headers=headers)).json()["data"]["id"]

    write_jobs_csv(tmp_path / "jobs.csv", [job_row()])
    await ingest_dataset(session, path=str(tmp_path / "jobs.csv"))

    profiles = (await session.execute(select(func.count()).select_from(Profile))).scalar_one()
    resumes = (await session.execute(select(func.count()).select_from(Resume))).scalar_one()

    assert profiles == 1
    assert resumes == 0
    after = (await client.get("/api/v1/profiles/me", headers=headers)).json()["data"]
    assert after["id"] == profile_id
    assert after["skills"] == []
