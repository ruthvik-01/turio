"""Async database engine, session factory and the request-scoped session."""

from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine(database_url: str, *, statement_timeout_ms: int | None = None) -> AsyncEngine:
    # pool_pre_ping is deliberately off. It issues a `SELECT 1` before every
    # checkout, and against the remote database that is a full round trip on
    # every request: measured 1.63s/request with it against 1.22s without.
    # pool_recycle covers the case it was there for - a connection the server
    # or pooler has dropped - by retiring connections before they go stale.
    connect_args = {}
    if statement_timeout_ms is not None and database_url.startswith("postgresql"):
        # The worker's statements are long by nature: ranking reads the whole
        # inventory and encodes it. The server default (2 min on Supabase) is
        # meant for interactive requests, so the worker raises it explicitly
        # rather than letting a legitimate batch be cancelled mid-run.
        # `options` is a libpq argument; SQLite rejects it, hence the guard.
        connect_args["options"] = f"-c statement_timeout={statement_timeout_ms}"
    return create_async_engine(
        database_url,
        connect_args=connect_args,
        pool_size=5,
        max_overflow=5,
        pool_recycle=300,
        pool_timeout=10,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a session bound to the application engine."""
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        yield session
