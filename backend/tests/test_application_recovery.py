import asyncio
from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import update

from app.core.errors import AppError
from app.core.time import utcnow
from app.models.application import Application
from app.services import application_operations, applications
from test_applications import flow, prepared


@pytest.mark.parametrize("status,kind,expected", [
    ("preparing", "prepare", "automation_failed"),
    ("preparing", "review", "automation_failed"),
    ("submitting", "submit", "verification_failed"),
])
async def test_expired_operation_is_recovered_once(client, session, flow, status, kind, expected):
    headers, app, _ = flow
    await session.execute(update(Application).where(Application.id == UUID(app["id"])).values(
        status=status, operation_kind=kind, operation_token=uuid4(),
        operation_expires_at=utcnow() - timedelta(seconds=1), review_token="x" * 64))
    await session.commit()
    response = await client.post(f"/api/v1/applications/{app['id']}/recover", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == expected and data["review_token"] is None
    assert data["operation_kind"] is None
    again = await client.post(f"/api/v1/applications/{app['id']}/recover", headers=headers)
    assert len(again.json()["data"]["events"]) == len(data["events"])


async def test_live_operation_and_other_owner_are_not_recovered(client, session, flow):
    from support import auth_headers
    headers, app, _ = flow
    await session.execute(update(Application).where(Application.id == UUID(app["id"])).values(
        status="preparing", operation_kind="prepare", operation_token=uuid4(),
        operation_expires_at=utcnow() + timedelta(seconds=60)))
    await session.commit()
    result = await client.post(f"/api/v1/applications/{app['id']}/recover", headers=headers)
    assert result.json()["data"]["status"] == "preparing"
    other = await auth_headers(client, "recovery-other@example.com")
    assert (await client.post(f"/api/v1/applications/{app['id']}/recover", headers=other)).status_code == 404


async def test_stale_handler_cannot_overwrite_new_operation(session, flow):
    _, data, _ = flow
    app = await session.get(Application, UUID(data["id"]))
    old = application_operations.begin(app, "prepare")
    app.status = "preparing"
    await session.commit()
    newer = application_operations.begin(app, "review")
    await session.commit()
    with pytest.raises(AppError):
        await applications.guard_operation(session, app, old)
    await session.refresh(app)
    assert app.operation_token == newer and app.status == "preparing"


async def test_uncertain_submission_replay_returns_recovered_failure(client, session, flow):
    headers, app, adapter = flow
    prefix = await prepared(client, headers, app)
    review = (await client.post(prefix + "/review", headers=headers)).json()["data"]
    started = asyncio.Event()

    async def hang(url, snapshot):
        started.set()
        await asyncio.Event().wait()

    adapter.submit = hang
    payload = {"approved": True, "review_token": review["review_token"]}
    approval_headers = {**headers, "Idempotency-Key": "interrupted-submit"}
    request = asyncio.create_task(client.post(prefix + "/approve-submit", headers=approval_headers, json=payload))
    await started.wait()
    await session.execute(update(Application).where(Application.id == UUID(app["id"])).values(
        operation_expires_at=utcnow() - timedelta(seconds=1)))
    await session.commit()
    recovered = await client.post(prefix + "/recover", headers=headers)
    assert recovered.json()["data"]["status"] == "verification_failed"
    request.cancel()
    await asyncio.gather(request, return_exceptions=True)
    repeated = await client.post(prefix + "/approve-submit", headers=approval_headers, json=payload)
    assert repeated.status_code == 200
    assert repeated.json()["data"]["status"] == "verification_failed"
    assert not adapter.submissions
