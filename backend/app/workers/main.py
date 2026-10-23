"""Database worker. Claims are durable; interrupted work is never auto-replayed."""

import argparse
import asyncio
import logging
import sys
from contextlib import suppress
from uuid import uuid4

from app.core.config import get_settings
from app.core.db import create_engine, create_session_factory
from app.core.errors import AppError
from app.core.logging import configure_logging
from app.repositories import runs as repo
from app.schemas.run import RunCreate
from app.services import applications, job_ingestion, jobs, matching

logger = logging.getLogger(__name__)


async def execute(factory, run):
    async with factory() as session:
        await repo.require_lease(session, run.id, run.lease_token)

        async def checkpoint():
            # Held through the service's next commit on PostgreSQL, so an
            # expired worker cannot commit that batch after recovery wins.
            await repo.require_lease(session, run.id, run.lease_token, lock=True)

        request = RunCreate(kind=run.run_type, **run.payload)
        if request.kind == "jobs_refresh":
            summary = await job_ingestion.ingest_dataset(session, checkpoint=checkpoint)
            return jobs.to_refresh_result(summary).model_dump(mode="json")
        if request.kind == "matches_refresh":
            result = await matching.generate(session, run.user_id, request.method, checkpoint=checkpoint)
            return result.model_dump(mode="json")
        # No dynamic dispatch or browser/submission execution.
        raise AppError("INVALID_REQUEST", "Unsupported background work.", 422)


async def heartbeat(factory, run, lease_seconds):
    failures = 0
    while True:
        await asyncio.sleep(lease_seconds / 3 if failures == 0 else lease_seconds / 6)
        try:
            async with factory() as session:
                renewed = await asyncio.wait_for(repo.renew(session, run.id, run.lease_token, lease_seconds),
                                                 timeout=min(10, lease_seconds / 3))
            if not renewed:
                return
            failures = 0
        except Exception:
            failures += 1
            if failures >= 3:
                return


async def process(factory, run, lease_seconds):
    work = asyncio.create_task(execute(factory, run))
    pulse = asyncio.create_task(heartbeat(factory, run, lease_seconds))
    try:
        done, _ = await asyncio.wait({work, pulse}, return_when=asyncio.FIRST_COMPLETED)
        if work not in done:
            work.cancel()
            await asyncio.gather(work, return_exceptions=True)
            async with factory() as session:
                await repo.interrupt(session, run.id, run.lease_token)
            return
        try:
            result, error = work.result(), None
        except AppError as exc:
            result, error = None, exc
        except Exception as exc:
            original = getattr(exc, "orig", None)
            logger.warning("run_execution_failed", extra={"extra_fields": {
                "run_id": str(run.id), "error_type": type(exc).__name__,
                "sqlstate": getattr(original, "sqlstate", None),
            }})
            result, error = None, AppError("INTERNAL_ERROR", "Background work failed. Check the worker configuration.", 500)
        async with factory() as session:
            saved = await repo.finish(session, run.id, run.lease_token, result=result, error=error)
            if not saved:
                await repo.interrupt(session, run.id, run.lease_token)
    except asyncio.CancelledError:
        work.cancel()
        await asyncio.gather(work, return_exceptions=True)
        try:
            async with factory() as session:
                await repo.interrupt(session, run.id, run.lease_token)
        except Exception:
            # A later worker will recover the expired lease after DB recovery.
            logger.warning("shutdown_interruption_record_pending")
        raise
    finally:
        pulse.cancel()
        await asyncio.gather(pulse, return_exceptions=True)


async def run_once(factory, worker_id, lease_seconds=None):
    lease_seconds = lease_seconds or get_settings().worker_lease_seconds
    async with factory() as session:
        await applications.recover_expired_operations(session)
        await repo.recover_expired(session)
        run = await repo.claim(session, worker_id, lease_seconds)
    if run is None:
        return None
    logger.info("run_started", extra={"extra_fields": {"run_id": str(run.id), "kind": run.run_type}})
    await process(factory, run, lease_seconds)
    async with factory() as session:
        finished = await repo.owned(session, run.user_id, run.id)
        logger.info("run_finished", extra={"extra_fields": {"run_id": str(run.id), "state": finished.state}})
        return finished.state


async def serve(factory, worker_id=None):
    worker_id = worker_id or uuid4().hex
    while True:
        try:
            result = await run_once(factory, worker_id)
        except Exception as exc:
            # Do not log exception text/SQL parameters containing candidate data.
            logger.warning("worker_iteration_failed", extra={"extra_fields": {"error_type": type(exc).__name__}})
            result = None
        if result is None:
            await asyncio.sleep(get_settings().worker_poll_seconds)


async def main(once):
    configure_logging()
    engine = create_engine(get_settings().database_url)
    try:
        factory = create_session_factory(engine)
        if once:
            result = await run_once(factory, uuid4().hex)
            return 1 if result in {"failed", "interrupted"} else 0
        await serve(factory)
        return 0
    finally:
        await engine.dispose()


if __name__ == "__main__":
    # Database-only worker: psycopg requires Selector on Windows. Browser
    # subprocesses are deliberately not dispatched by this worker.
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    with suppress(KeyboardInterrupt):
        raise SystemExit(asyncio.run(main(args.once)))
