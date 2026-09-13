"""Phase 0 exit checklist item (a): `/health` performs a real database ping.

Together these are the evidence. The unavailable-database case fails if the
endpoint is ever replaced with a hardcoded response; the working-database case
covers the success envelope and the request id wiring.
"""

from httpx import AsyncClient


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
