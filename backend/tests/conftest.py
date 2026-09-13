"""Shared test fixtures.

`app.main` reads DATABASE_URL while the module is being imported, so the
placeholder below must be set before that import. Tests that need a specific
database override the `get_session` dependency instead of touching the
environment.
"""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://turio:turio@127.0.0.1:1/turio")

from collections.abc import AsyncIterator  # noqa: E402

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.db import get_session  # noqa: E402
from app.main import create_app  # noqa: E402

# Port 1 is closed, so connecting fails immediately rather than hanging.
UNREACHABLE_DATABASE_URL = "postgresql+psycopg://turio:turio@127.0.0.1:1/turio"


def _client_bound_to(engine: AsyncEngine) -> AsyncClient:
    """An ASGI client whose request session comes from `engine`."""
    app = create_app()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _override() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture
async def database_down_client() -> AsyncIterator[AsyncClient]:
    """Client whose session is backed by an unreachable PostgreSQL server."""
    engine = create_async_engine(
        UNREACHABLE_DATABASE_URL, connect_args={"connect_timeout": 2}
    )
    try:
        async with _client_bound_to(engine) as client:
            yield client
    finally:
        await engine.dispose()


@pytest.fixture
async def database_up_client() -> AsyncIterator[AsyncClient]:
    """Client whose session is backed by a real, working engine.

    SQLite stands in for PostgreSQL here so this suite can run without Docker.
    It exercises the same repository `SELECT 1` through the same SQLAlchemy
    session; the PostgreSQL round trip itself is verified by the Phase 0
    compose check.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with _client_bound_to(engine) as client:
            yield client
    finally:
        await engine.dispose()
