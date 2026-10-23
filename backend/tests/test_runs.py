"""Durable worker/API checks on isolated SQL fixtures, not PostgreSQL evidence."""

import asyncio
from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.time import utcnow
from app.models.job import Job
from app.models.run import AgentRun
from app.repositories import runs as repo
from app.services.job_ingestion import ingest_dataset
from app.workers import main as worker
from support import auth_headers, job_row, write_jobs_csv


async def enqueue(client, headers, kind="matches_refresh", key="one", **payload):
    return await client.post("/api/v1/runs", headers={**headers, "Idempotency-Key": key},
                             json={"kind": kind, **payload})


@pytest.fixture
def factory(database_engine):
    return async_sessionmaker(database_engine, expire_on_commit=False)


async def test_enqueue_is_durable_idempotent_and_aliases_active_work(client):
    headers = await auth_headers(client)
    first = await enqueue(client, headers)
    assert first.status_code == 202, first.text
    run = first.json()["data"]
    assert run["state"] == "queued" and run["result"] is None
    assert (await enqueue(client, headers)).json()["data"]["id"] == run["id"]
    alias = await enqueue(client, headers, key="alias", method="keyword")
    assert alias.json()["data"]["id"] == run["id"]
    changed = await enqueue(client, headers, method="sbert")
    assert changed.status_code == 409
    listing = (await client.get("/api/v1/runs?state=queued", headers=headers)).json()["data"]
    assert listing["total"] == 1
    await client.post(f"/api/v1/runs/{run['id']}/cancel", headers=headers)
    replayed_alias = await enqueue(client, headers, key="alias", method="keyword")
    assert replayed_alias.json()["data"]["id"] == run["id"]
    assert replayed_alias.json()["data"]["state"] == "cancelled"


async def test_queue_rejects_submissions_paths_and_missing_keys(client):
    headers = await auth_headers(client)
    for body in ({"kind": "application_submit"}, {"kind": "jobs_refresh", "path": "secret.txt"},
                 {"kind": "jobs_refresh", "method": "sbert"}):
        response = await client.post("/api/v1/runs", headers={**headers, "Idempotency-Key": "invalid"}, json=body)
        assert response.status_code == 422
    assert (await client.post("/api/v1/runs", headers=headers, json={"kind": "jobs_refresh"})).status_code == 422
    assert (await client.get("/api/v1/runs")).status_code == 401


async def test_run_ownership_and_global_inventory_lock_do_not_leak(client):
    first_user = await auth_headers(client)
    other_user = await auth_headers(client, "other-worker@example.com")
    run = (await enqueue(client, first_user, kind="jobs_refresh")).json()["data"]
    assert (await client.get(f"/api/v1/runs/{run['id']}", headers=other_user)).status_code == 404
    assert (await client.post(f"/api/v1/runs/{run['id']}/cancel", headers=other_user)).status_code == 404
    assert (await enqueue(client, other_user, kind="jobs_refresh")).status_code == 409
    assert (await client.get("/api/v1/runs", headers=other_user)).json()["data"]["total"] == 0


async def test_cancel_only_queued_and_replay_keeps_identity(client, factory):
    headers = await auth_headers(client)
    run = (await enqueue(client, headers)).json()["data"]
    cancelled = await client.post(f"/api/v1/runs/{run['id']}/cancel", headers=headers)
    assert cancelled.json()["data"]["state"] == "cancelled"
    assert (await enqueue(client, headers)).json()["data"]["state"] == "cancelled"
    assert await worker.run_once(factory, "fixture") is None
    fresh = (await enqueue(client, headers, key="fresh")).json()["data"]
    async with factory() as session:
        claimed = await repo.claim(session, "fixture", 60)
    assert str(claimed.id) == fresh["id"]
    assert (await client.post(f"/api/v1/runs/{fresh['id']}/cancel", headers=headers)).status_code == 409


async def test_atomic_claim_has_only_one_winner(client, factory):
    headers = await auth_headers(client)
    await enqueue(client, headers)

    async def claim(name):
        async with factory() as session:
            return await repo.claim(session, name, 60)

    first, second = await asyncio.gather(claim("one"), claim("two"))
    assert sum(run is not None for run in (first, second)) == 1


async def test_job_import_runs_and_reimport_is_a_noop(client, factory, tmp_path, monkeypatch):
    headers = await auth_headers(client)
    path = write_jobs_csv(tmp_path / "worker-jobs.csv", [job_row(), job_row(ats_id="worker-two")])
    monkeypatch.setattr(get_settings(), "job_dataset_path", str(path))
    first = (await enqueue(client, headers, kind="jobs_refresh")).json()["data"]
    assert await worker.run_once(factory, "first-process") == "succeeded"
    result = (await client.get(f"/api/v1/runs/{first['id']}", headers=headers)).json()["data"]
    assert result["result"]["inserted"] == 2
    second = (await enqueue(client, headers, kind="jobs_refresh", key="second")).json()["data"]
    assert await worker.run_once(factory, "restarted-process") == "succeeded"
    repeated = (await client.get(f"/api/v1/runs/{second['id']}", headers=headers)).json()["data"]["result"]
    assert repeated["inserted"] == repeated["updated"] == 0 and repeated["unchanged"] == 2


async def test_matching_worker_uses_existing_pipeline(client, session, factory, tmp_path):
    headers = await auth_headers(client)
    await client.patch("/api/v1/profiles/me", headers=headers, json={"skills": ["Python"], "preferred_roles": ["Python engineer"]})
    path = write_jobs_csv(tmp_path / "matching-worker.csv", [job_row()])
    await ingest_dataset(session, path=str(path))
    run = (await enqueue(client, headers)).json()["data"]
    assert await worker.run_once(factory, "match-process") == "succeeded"
    result = (await client.get(f"/api/v1/runs/{run['id']}", headers=headers)).json()["data"]
    assert result["result"]["matches"][0]["job"]["title"] == "Senior Python Engineer"


async def test_failures_are_persisted_and_not_automatically_retried(client, factory, monkeypatch):
    headers = await auth_headers(client)
    run = (await enqueue(client, headers)).json()["data"]

    async def fail(*args):
        raise RuntimeError("private provider content must not be returned")

    monkeypatch.setattr(worker, "execute", fail)
    assert await worker.run_once(factory, "failed-process") == "failed"
    result = await client.get(f"/api/v1/runs/{run['id']}", headers=headers)
    assert result.json()["data"]["error_code"] == "INTERNAL_ERROR"
    assert "private provider" not in result.text
    assert await worker.run_once(factory, "another-process") is None


async def test_expired_lease_is_interrupted_and_stale_worker_cannot_finish(client, factory):
    headers = await auth_headers(client)
    run_id = UUID((await enqueue(client, headers)).json()["data"]["id"])
    async with factory() as session:
        claimed = await repo.claim(session, "old-worker", 60)
        await session.execute(update(AgentRun).where(AgentRun.id == run_id).values(lease_expires_at=utcnow() - timedelta(seconds=1)))
        await session.commit()
    async with factory() as session:
        assert await repo.recover_expired(session) == 1
        assert not await repo.finish(session, run_id, claimed.lease_token, result={"incorrect": True})
        assert not await repo.renew(session, run_id, claimed.lease_token, 60)
        assert await repo.claim(session, "new-worker", 60) is None
    result = (await client.get(f"/api/v1/runs/{run_id}", headers=headers)).json()["data"]
    assert result["state"] == "interrupted" and result["result"] is None


async def test_heartbeat_renews_and_wrong_token_cannot_mutate(client, factory):
    headers = await auth_headers(client)
    await enqueue(client, headers)
    async with factory() as session:
        run = await repo.claim(session, "worker", 60)
        old_expiry = run.lease_expires_at
    async with factory() as session:
        assert not await repo.renew(session, run.id, uuid4(), 60)
        assert await repo.renew(session, run.id, run.lease_token, 120)
        row = await session.get(AgentRun, run.id)
        assert row.lease_expires_at > old_expiry


async def test_lost_heartbeat_cancels_work_without_replay(client, factory, monkeypatch):
    headers = await auth_headers(client)
    run = (await enqueue(client, headers)).json()["data"]
    started, stopped = asyncio.Event(), asyncio.Event()

    async def work(*args):
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            stopped.set()

    async def lost(*args):
        await started.wait()

    monkeypatch.setattr(worker, "execute", work)
    monkeypatch.setattr(worker, "heartbeat", lost)
    await worker.run_once(factory, "lost-worker")
    assert stopped.is_set()
    assert (await client.get(f"/api/v1/runs/{run['id']}", headers=headers)).json()["data"]["state"] == "interrupted"
    assert await worker.run_once(factory, "next-worker") is None


async def test_ingestion_checkpoint_rolls_back_uncommitted_batch(session, tmp_path):
    path = write_jobs_csv(tmp_path / "interrupted.csv", [job_row()])

    async def lost():
        raise AppError("RUN_INTERRUPTED", "Fixture lease lost.", 409)

    with pytest.raises(AppError):
        await ingest_dataset(session, path=str(path), checkpoint=lost)
    await session.rollback()
    assert list((await session.execute(select(Job))).scalars()) == []


async def test_matching_checkpoint_preserves_previous_results(client, session, tmp_path):
    from app.models.matching import JobMatch
    from app.services import matching

    headers = await auth_headers(client)
    user_id = UUID((await client.get("/api/v1/auth/me", headers=headers)).json()["data"]["id"])
    await client.patch("/api/v1/profiles/me", headers=headers, json={"skills": ["Python"]})
    path = write_jobs_csv(tmp_path / "fenced-matches.csv", [job_row()])
    await ingest_dataset(session, path=str(path))
    assert (await client.post("/api/v1/matches", headers=headers, json={})).status_code == 200
    previous = list((await session.execute(select(JobMatch.id))).scalars())
    await session.commit()
    await client.patch("/api/v1/profiles/me", headers=headers, json={"skills": ["Docker"]})

    async def lost():
        raise AppError("RUN_INTERRUPTED", "Fixture lease lost.", 409)

    with pytest.raises(AppError):
        await matching.generate(session, user_id, "keyword", checkpoint=lost)
    await session.rollback()
    assert list((await session.execute(select(JobMatch.id))).scalars()) == previous


async def test_worker_shutdown_records_interruption(client, factory, monkeypatch):
    headers = await auth_headers(client)
    run = (await enqueue(client, headers)).json()["data"]
    started = asyncio.Event()

    async def work(*args):
        started.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(worker, "execute", work)
    task = asyncio.create_task(worker.run_once(factory, "shutdown-worker"))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert (await client.get(f"/api/v1/runs/{run['id']}", headers=headers)).json()["data"]["state"] == "interrupted"


async def test_worker_cli_process_reads_saved_queue_without_replaying_completed_work(client, database_engine, tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path

    headers = await auth_headers(client)
    run = (await enqueue(client, headers, kind="jobs_refresh")).json()["data"]
    path = write_jobs_csv(tmp_path / "process-fixture.csv", [job_row()])
    environment = {**os.environ, "DATABASE_URL": database_engine.url.render_as_string(hide_password=False),
        "JOB_DATASET_PATH": str(path), "SECRET_KEY": "worker-process-fixture-only",
        "OBJECT_STORAGE_ENDPOINT": "http://storage.invalid", "OBJECT_STORAGE_BUCKET": "fixture",
        "OBJECT_STORAGE_ACCESS_KEY": "fixture", "OBJECT_STORAGE_SECRET_KEY": "fixture"}
    backend = Path(__file__).resolve().parents[1]
    command = [sys.executable, "-m", "app.workers.main", "--once"]
    first = subprocess.run(command, cwd=backend, env=environment, capture_output=True, text=True, timeout=30)
    assert first.returncode == 0, first.stderr
    result = (await client.get(f"/api/v1/runs/{run['id']}", headers=headers)).json()["data"]
    assert result["state"] == "succeeded" and result["result"]["inserted"] == 1
    second = subprocess.run(command, cwd=backend, env=environment, capture_output=True, text=True, timeout=30)
    assert second.returncode == 0, second.stderr
    assert "run_started" not in second.stdout
    assert (await client.get(f"/api/v1/runs/{run['id']}", headers=headers)).json()["data"] == result


@pytest.mark.parametrize("row_count, delay", [(80, 0.01), (2, 0.5)])
async def test_unchanged_import_keeps_heartbeat_responsive(client, session, factory, tmp_path, monkeypatch, row_count, delay):
    import time
    from app.services import job_ingestion

    headers = await auth_headers(client)
    path = write_jobs_csv(tmp_path / "slow-unchanged.csv", [job_row(ats_id=f"slow-{i}") for i in range(row_count)])
    await ingest_dataset(session, path=str(path))
    monkeypatch.setattr(get_settings(), "job_dataset_path", str(path))
    original = job_ingestion.normalize_row

    def slow_normalization(row):
        time.sleep(delay)  # Includes a single normalization longer than the lease.
        return original(row)

    monkeypatch.setattr(job_ingestion, "normalize_row", slow_normalization)
    run = (await enqueue(client, headers, kind="jobs_refresh")).json()["data"]
    assert await worker.run_once(factory, "responsive-worker", lease_seconds=0.4) == "succeeded"
    result = (await client.get(f"/api/v1/runs/{run['id']}", headers=headers)).json()["data"]
    assert result["result"]["unchanged"] == row_count


async def test_heartbeat_survives_transient_renewal_exception(factory, monkeypatch):
    from types import SimpleNamespace
    calls = 0

    async def flaky_renew(session, run_id, lease_token, lease_seconds):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("transient connection glitch")
        return calls == 2

    monkeypatch.setattr(worker.repo, "renew", flaky_renew)
    run = SimpleNamespace(id=uuid4(), lease_token=uuid4())
    await asyncio.wait_for(worker.heartbeat(factory, run, 0.06), timeout=2.0)
    assert calls == 3
