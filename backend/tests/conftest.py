"""Shared test fixtures.

`app.main` reads its settings while the module is being imported, so the
placeholders below must be set before that import. Tests that need a specific
database or object store override the relevant dependency instead of touching
the environment.
"""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://turio:turio@127.0.0.1:1/turio")
os.environ.setdefault("SECRET_KEY", "test-only-secret-key-never-used-outside-tests")
os.environ.setdefault("OBJECT_STORAGE_ENDPOINT", "http://object-storage.invalid:9000")
os.environ.setdefault("OBJECT_STORAGE_BUCKET", "turio-test")
os.environ.setdefault("OBJECT_STORAGE_ACCESS_KEY", "test-access-key")
os.environ.setdefault("OBJECT_STORAGE_SECRET_KEY", "test-secret-key")

from collections.abc import AsyncIterator, Callable  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.deps import get_storage  # noqa: E402
from app.core.db import get_session  # noqa: E402
from app.core.errors import AppError  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import Base  # noqa: E402
from app.services.resume_parser import ParsedResume  # noqa: E402

# Port 1 is closed, so connecting fails immediately rather than hanging.
UNREACHABLE_DATABASE_URL = "postgresql+psycopg://turio:turio@127.0.0.1:1/turio"


class InMemoryStorage:
    """Stands in for S3 so upload tests need no object-storage service.

    Records the keys it was asked to store, which is how the "same bytes are
    not stored twice" check is asserted.
    """

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.put_calls: list[str] = []
        # Set by a test that needs to see how an object-storage outage surfaces.
        self.fail = False

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        if self.fail:
            raise AppError(
                "OBJECT_STORAGE_UNAVAILABLE", "The uploaded file could not be stored.", 503
            )
        self.put_calls.append(key)
        self.objects[key] = data


def build_pdf(text: str) -> bytes:
    """Build a minimal single-page PDF containing `text`, one line per row.

    Written by hand rather than pulled from a generator library so that the
    upload path can be tested against genuine PDF bytes with no extra
    dependency.
    """
    content_lines = ["BT", "/F1 11 Tf", "14 TL", "72 720 Td"]
    for line in text.split("\n"):
        escaped = line.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
        content_lines.append(f"({escaped}) Tj T*")
    content_lines.append("ET")
    content = "\n".join(content_lines).encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length "
        + str(len(content)).encode()
        + b" >>\nstream\n"
        + content
        + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for index, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{index} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_offset = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode()
    return bytes(out)


@pytest.fixture
def make_pdf() -> Callable[[str], bytes]:
    return build_pdf


@pytest.fixture
def storage() -> InMemoryStorage:
    return InMemoryStorage()


def _client_bound_to(engine: AsyncEngine, storage: InMemoryStorage) -> AsyncClient:
    """An ASGI client whose session and object store are both substituted."""
    app = create_app()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _session_override() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _session_override
    app.dependency_overrides[get_storage] = lambda: storage
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture
async def database_down_client(storage: InMemoryStorage) -> AsyncIterator[AsyncClient]:
    """Client whose session is backed by an unreachable PostgreSQL server."""
    engine = create_async_engine(
        UNREACHABLE_DATABASE_URL, connect_args={"connect_timeout": 2}
    )
    try:
        async with _client_bound_to(engine, storage) as client:
            yield client
    finally:
        await engine.dispose()


@pytest.fixture
async def database_up_client(storage: InMemoryStorage) -> AsyncIterator[AsyncClient]:
    """Client whose session is backed by a real, working engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with _client_bound_to(engine, storage) as client:
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
async def client(
    database_engine: AsyncEngine, storage: InMemoryStorage
) -> AsyncIterator[AsyncClient]:
    """Authenticated-flow client: real schema, real SQL, no external services."""
    async with _client_bound_to(database_engine, storage) as http_client:
        yield http_client


@pytest.fixture
def empty_parse() -> ParsedResume:
    """A parse that found nothing, for the no-fabrication assertions."""
    return ParsedResume()
