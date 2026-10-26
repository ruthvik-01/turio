"""Bounded text-only choice decisions. No execution or generated values."""

import asyncio
import hashlib
import json
import logging
import math
from contextlib import asynccontextmanager
from weakref import WeakKeyDictionary

import httpx
from sqlalchemy import text

from app.core.config import get_settings
from app.core.errors import AppError
from app.services import rate_limits

logger = logging.getLogger(__name__)
_local_active = WeakKeyDictionary()  # SQLite fixtures only; production uses PostgreSQL.


class InvalidResponse(ValueError):
    pass


def supported(decision):
    if not decision or 'confidence' not in decision:
        return False
    value = decision['confidence']
    return value is None or (type(value) in (int, float) and math.isfinite(value) and 0.50 <= value <= 1)


def uncertain(decision):
    value = decision.get('confidence')
    return value is None or value < 0.90


def make_client():
    return httpx.AsyncClient(timeout=15, follow_redirects=False, trust_env=False)


class AssistanceOperation:
    """Shared batching, deadline and request budget. Providers supply body/request."""

    provider = 'openrouter'
    model = ''

    def __init__(self, enabled):
        self.enabled = enabled
        self.deadline = asyncio.get_running_loop().time() + 15
        self.status = "complete" if enabled else "unavailable"
        self.overflow = 0
        self.requests = 0
        self.error_code = None

    def body(self, items):
        raise NotImplementedError

    def fits(self, items):
        raise NotImplementedError

    async def request(self, body):
        raise NotImplementedError

    async def evaluate(self, items):
        if not self.enabled or self.status != 'complete':
            return {}
        batches, batch = [], []
        for item in items:
            if not self.fits([item]):
                self.overflow += 1
                continue
            if not self.fits(batch + [item]):
                batches.append(batch)
                batch = []
            batch.append(item)
        if batch:
            batches.append(batch)
        remaining = max(0, 3 - self.requests)
        self.overflow += sum(len(b) for b in batches[remaining:])
        result = {}
        started = asyncio.get_running_loop().time()
        try:
            async with asyncio.timeout_at(self.deadline):
                for batch in batches[:remaining]:
                    self.requests += 1
                    result.update(await self.request(self.body(batch)))
        except (httpx.HTTPError, InvalidResponse, ValueError, TypeError, TimeoutError) as exc:
            self.status = "unavailable"
            self.error_code = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else type(exc).__name__
        logger.info("ai_assistance", extra={"extra_fields": {"provider": self.provider, "model": self.model, "status": self.status, "error_code": self.error_code,
            "duration_ms": round((asyncio.get_running_loop().time() - started) * 1000), "overflow": self.overflow}})
        return result


@asynccontextmanager
async def assistance(session, user_id):
    await rate_limits.work(session, user_id)
    from app.adapters.openrouter import OpenRouterOperation
    op = OpenRouterOperation(get_settings().assistance_enabled)
    if not op.enabled:
        yield op
        return
    engine = session.bind
    key = int.from_bytes(hashlib.sha256(f"turio:ai:{user_id}".encode()).digest()[:8], "big", signed=True)
    if engine.dialect.name != "postgresql":
        active = _local_active.setdefault(engine, set())
        if key in active:
            raise AppError("RATE_LIMITED", "AI assistance is already running. Try again shortly.", 429)
        active.add(key)
        try:
            yield op
        finally:
            active.remove(key)
        return
    async with engine.connect() as connection:
        try:
            acquired = await connection.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": key})
        except BaseException:
            # Cancellation may arrive after PostgreSQL acquired the session
            # lock but before the response reached us. Never pool that session.
            await connection.invalidate()
            raise
        if not acquired:
            raise AppError("RATE_LIMITED", "AI assistance is already running. Try again shortly.", 429)
        try:
            yield op
        finally:
            async def release():
                try:
                    await connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": key})
                    await connection.commit()
                except BaseException:
                    await connection.invalidate()
                    raise
            cleanup = asyncio.create_task(release())
            try:
                await asyncio.shield(cleanup)
            except asyncio.CancelledError:
                await cleanup
                raise
