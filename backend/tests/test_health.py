"""Phase 0 exit checklist item (a): `/health` performs a real database ping.

Together these are the evidence. The unavailable-database case fails if the
endpoint is ever replaced with a hardcoded response; the working-database case
covers the success envelope and the request id wiring.
"""

from httpx import AsyncClient
import asyncio

import pytest
from sqlalchemy.exc import OperationalError

from app.core.errors import AppError
from app.services import health as health_service
from app.services.health import check_health


async def test_health_reports_database_unavailable_when_ping_fails(
    database_down_client: AsyncClient,
) -> None:
    response = await database_down_client.get("/api/v1/health")

    assert response.status_code == 503
    body = response.json()
    assert body["data"] is None
    assert body["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert body["request_id"]


async def test_health_returns_ok_envelope_when_database_responds(
    database_up_client: AsyncClient,
) -> None:
    response = await database_up_client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["status"] == "ok"
    assert body["data"]["database"] == "ok"
    assert body["data"]["version"]
    assert body["request_id"]


async def test_inbound_request_id_is_echoed(database_up_client: AsyncClient) -> None:
    response = await database_up_client.get(
        "/api/v1/health", headers={"X-Request-ID": "phase-0-test-request-id"}
    )

    assert response.headers["X-Request-ID"] == "phase-0-test-request-id"
    assert response.json()["request_id"] == "phase-0-test-request-id"


async def test_health_succeeds_when_ping_is_slower_than_a_local_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A cold remote pooler connection takes 4-5 seconds; it must not be a 503."""

    async def slow_ping(_session: object) -> None:
        await asyncio.sleep(4.5)

    monkeypatch.setattr(health_service, "ping", slow_ping)

    data = await check_health(object())

    assert data.status == "ok"
    assert data.database == "ok"


async def test_health_reports_unavailable_when_ping_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def failing_ping(_session: object) -> None:
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    monkeypatch.setattr(health_service, "ping", failing_ping)

    with pytest.raises(AppError) as exc_info:
        await check_health(object())

    assert exc_info.value.code == "DATABASE_UNAVAILABLE"
    assert exc_info.value.http_status == 503


async def test_health_times_out_when_ping_exceeds_the_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def hung_ping(_session: object) -> None:
        await asyncio.sleep(5)

    monkeypatch.setattr(health_service, "ping", hung_ping)
    monkeypatch.setattr(health_service, "PING_TIMEOUT_SECONDS", 0.05)

    with pytest.raises(AppError) as exc_info:
        await check_health(object())

    assert exc_info.value.code == "DATABASE_UNAVAILABLE"
    assert exc_info.value.http_status == 503


def test_ping_timeout_allows_a_cold_remote_connection() -> None:
    """Guards the constant: Supabase's pooler needs ~4-5s on a cold connect."""
    assert health_service.PING_TIMEOUT_SECONDS >= 10.0
