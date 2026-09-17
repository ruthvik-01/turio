"""Disposable UI test server. Never uses or verifies the deployment database."""

import os
import asyncio
import copy
import hashlib
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

if os.environ.get("TURIO_UI_TEST") != "1":
    raise RuntimeError("This fixture server requires TURIO_UI_TEST=1. Do not deploy it.")

from conftest import InMemoryStorage  # noqa: E402; supplies test-only settings
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.api.deps import get_storage
from app.core.config import get_settings
from app.main import create_app
from app.models import Base
from app.models.resume import Resume
from app.api.v1.applications import get_adapter
from app.services.job_ingestion import ingest_dataset
from app.workers.main import serve
from support import job_row, write_jobs_csv


@asynccontextmanager
async def lifespan(app):
    with TemporaryDirectory(prefix="turio-ui-fixture-") as directory:
        engine = create_async_engine(f"sqlite+aiosqlite:///{Path(directory).as_posix()}/fixture.db")
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        app.state.engine, app.state.session_factory = engine, factory
        path = write_jobs_csv(Path(directory) / "fixture.csv", [
            job_row(ats_id="ui-python", title="Python Engineer", company="UI Fixture Labs", description="Python, FastAPI and PostgreSQL. Synthetic UI test posting."),
            job_row(ats_id="ui-design", title="Graphic Designer", company="UI Fixture Studio", description="Illustration and typography. Synthetic UI test posting."),
        ])
        async with factory() as session:
            await ingest_dataset(session, path=str(path))
        settings = get_settings()
        old_path, old_poll = settings.job_dataset_path, settings.worker_poll_seconds
        settings.job_dataset_path, settings.worker_poll_seconds = str(path), 0.05
        worker = asyncio.create_task(serve(factory, "ui-fixture-worker"))
        print("TURIO UI FIXTURE: disposable SQLite and in-memory storage; NOT PostgreSQL verification.", flush=True)
        try:
            yield
        finally:
            worker.cancel()
            await asyncio.gather(worker, return_exceptions=True)
            settings.job_dataset_path, settings.worker_poll_seconds = old_path, old_poll
            await engine.dispose()


app = create_app()
app.router.lifespan_context = lifespan
storage = InMemoryStorage()
app.dependency_overrides[get_storage] = lambda: storage

application_fixture = os.environ.get("TURIO_UI_APPLICATION_FIXTURE") == "1"

if application_fixture:
    from test_applications import FakeAdapter, FORM

    class UIAdapter(FakeAdapter):
        """No network operations. Used only by the disposable UI test server."""

        async def inspect(self, url):
            schema = copy.deepcopy(FORM)
            schema["fields"].extend([
                {"field_key": "resume", "label": "Resume", "input_type": "file",
                 "required": True, "source_locator": "#resume", "options": []},
                {"field_key": "background", "label": "Describe your relevant experience",
                 "input_type": "textarea", "required": False, "source_locator": "#background", "options": []},
            ])
            return schema

        async def fill(self, url, snapshot):
            async with app.state.session_factory() as session:
                resume = await session.get(Resume, UUID(snapshot["resume_id"]))
                original = await storage.get(resume.storage_key)
                assert hashlib.sha256(original).hexdigest() == resume.checksum
                assert snapshot["answers"]["resume"] == str(resume.id)
            await super().fill(url, snapshot)

        async def submit(self, url, snapshot):
            assert snapshot == self.fills[-1]
            return await super().submit(url, snapshot)

    adapter = UIAdapter()
    app.dependency_overrides[get_adapter] = lambda: adapter


@app.get("/api/v1/health/fixture")
async def fixture_info():
    return {"fixture": "turio-disposable-ui", "application_fixture": application_fixture,
            "submissions": len(adapter.submissions) if application_fixture else 0,
            "resume_writes": len(storage.put_calls), "resume_reads": len(storage.get_calls)}
