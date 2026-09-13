#!/usr/bin/env python
"""Ingest the job dataset without going through HTTP.

`POST /api/v1/jobs/refresh` exists, but the initial load is 55k rows taking
minutes, which is a poor fit for a request. This runs the same service function
so the two paths cannot diverge.

Usage, from the repository root:

    backend/.venv/Scripts/python scripts/import_jobs.py [path/to/jobs.csv]

`DATABASE_URL`, `SECRET_KEY` and the `OBJECT_STORAGE_*` variables must be set
(or present in backend/.env), because the application settings are loaded on
import.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.db import create_engine, create_session_factory  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.services.job_ingestion import ingest_dataset  # noqa: E402


async def main(path: str | None) -> int:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    try:
        async with session_factory() as session:
            summary = await ingest_dataset(session, path=path)
    finally:
        await engine.dispose()

    print(
        f"read={summary.rows_read} inserted={summary.inserted} "
        f"updated={summary.updated} unchanged={summary.unchanged} "
        f"rejected={summary.rejected}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else None)))
