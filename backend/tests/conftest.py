"""Shared test fixtures.

`app.main` reads its settings while the module is being imported, so the
placeholders below must be set before that import. Tests that need a specific
database override the `get_session` dependency instead of touching the
environment.
"""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://turio:turio@127.0.0.1:1/turio")
os.environ.setdefault("SECRET_KEY", "test-only-secret-key-never-used-outside-tests")

from collections.abc import AsyncIterator  # noqa: E402
from pathlib import Path  # noqa: E402

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
from app.models import Base  # noqa: E402

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
    """Client whose session is backed by a real, working engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with _client_bound_to(engine) as client:
            yield client
    finally:
        await engine.dispose()


@pytest.fixture
async def database_engine(tmp_path: Path) -> AsyncIterator[AsyncEngine]:
    """An engine with the full schema created, for tests that need real SQL.

    A file rather than `:memory:` so every pooled connection sees the same
    database. PostgreSQL is the deployment target; SQLite stands in here so
    that the suite runs without a container runtime.
    """
    url = f"sqlite+aiosqlite:///{(tmp_path / 'turio-test.db').as_posix()}"
    engine = create_async_engine(url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def client(database_engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    """Authenticated-flow client: real schema, real SQL, no external services."""
    async with _client_bound_to(database_engine) as http_client:
        yield http_client
