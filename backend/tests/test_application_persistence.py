"""Stable preparation and atomic answer writes against real database fixtures."""

import copy
from uuid import UUID

import pytest
from sqlalchemy import select

from app.models.application import Application, ApplicationAnswer, ApplicationField
from test_applications import FORM, flow, prepared


async def test_reprepare_preserves_answers_and_field_ids(client, flow):
    headers, app, _ = flow
    prefix = await prepared(client, headers, app)
    before = (await client.get(prefix, headers=headers)).json()["data"]
    again = await client.post(prefix + "/start", headers=headers)
    assert again.status_code == 200, again.text
    after = again.json()["data"]
    assert after["fields"] == before["fields"]
    field = next(f for f in before["fields"] if f["field_key"] == "authorization")
    saved = await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": "old-field-id"},
        json={"answers": [{"field_id": field["id"], "value": "Updated", "save_for_reuse": False}]})
    assert saved.status_code == 200, saved.text


async def test_reprepare_updates_metadata_and_removes_retired_fields(client, flow, session):
    headers, app, adapter = flow
    prefix = await prepared(client, headers, app)
    before = (await client.get(prefix, headers=headers)).json()["data"]
    schema = copy.deepcopy(FORM)
    schema["fields"] = schema["fields"][:2]
    schema["fields"][0]["source_locator"] = "#updated-name"
    schema["fields"][0]["required"] = False
    schema["fields"].append({"field_key": "new", "label": "New question", "input_type": "text",
                             "required": True, "source_locator": "#new", "options": []})
    async def inspect(url):
        return copy.deepcopy(schema)
    adapter.inspect = inspect
    result = await client.post(prefix + "/start", headers=headers)
    assert result.status_code == 200, result.text
    fields = {f["field_key"]: f for f in result.json()["data"]["fields"]}
    assert set(fields) == {"name", "email", "new"}
    assert fields["name"]["id"] == next(f["id"] for f in before["fields"] if f["field_key"] == "name")
    assert fields["name"]["required"] is False
    name = await session.get(ApplicationField, UUID(fields["name"]["id"]))
    assert name.source_locator == "#updated-name"
    retired = UUID(next(f["id"] for f in before["fields"] if f["field_key"] == "authorization"))
    assert await session.get(ApplicationField, retired) is None
    assert await session.get(ApplicationAnswer, retired) is None


async def test_stale_answer_revision_rejected_and_success_replayed(client, flow):
    headers, app, _ = flow
    prefix = await prepared(client, headers, app)
    before = (await client.get(prefix, headers=headers)).json()["data"]
    field = next(f for f in before["fields"] if f["field_key"] == "authorization")
    payload = {"expected_revision": before["revision"],
               "answers": [{"field_id": field["id"], "value": "First", "save_for_reuse": False}]}
    key = {**headers, "Idempotency-Key": "revision-first"}
    saved = await client.post(prefix + "/answers", headers=key, json=payload)
    assert saved.status_code == 200, saved.text
    assert saved.json()["data"]["revision"] == before["revision"] + 1
    replay = await client.post(prefix + "/answers", headers=key, json=payload)
    assert replay.json()["data"] == saved.json()["data"]
    payload["answers"][0]["value"] = "Stale"
    stale = await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": "revision-stale"}, json=payload)
    assert stale.status_code == 409, stale.text
    assert stale.json()["error"]["code"] == "STALE_REVISION"
    assert (await client.get(prefix, headers=headers)).json()["data"] == saved.json()["data"]


async def test_invalid_batch_does_not_save_answers_reuse_or_events(client, flow):
    headers, app, _ = flow
    prefix = await prepared(client, headers, app)
    before = (await client.get(prefix, headers=headers)).json()["data"]
    fields = {f["field_key"]: f for f in before["fields"]}
    response = await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": "invalid-batch"},
        json={"expected_revision": before["revision"], "answers": [
            {"field_id": fields["authorization"]["id"], "value": "Must roll back"},
            {"field_id": fields["email"]["id"], "value": "invalid-email"}]})
    assert response.status_code == 422, response.text
    assert (await client.get(prefix, headers=headers)).json()["data"] == before
    other = (await client.post("/api/v1/applications", headers={**headers, "Idempotency-Key": "after-invalid"},
        json={"job_id": app["job"]["id"]})).json()["data"]
    result = (await client.post(f'/api/v1/applications/{other["id"]}/start', headers=headers)).json()["data"]
    assert next(f for f in result["fields"] if f["field_key"] == "authorization")["value"] is None


async def test_answer_edit_does_not_lock_user_or_unrelated_draft(client, flow, database_engine):
    from sqlalchemy import event
    headers, app, _ = flow
    prefix = await prepared(client, headers, app)
    data = (await client.get(prefix, headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "authorization")
    statements = []
    def capture(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement)
    event.listen(database_engine.sync_engine, "before_cursor_execute", capture)
    try:
        response = await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": "scoped-write"},
            json={"answers": [{"field_id": field["id"], "value": "Yes", "save_for_reuse": False}]})
        assert response.status_code == 200, response.text
    finally:
        event.remove(database_engine.sync_engine, "before_cursor_execute", capture)
    assert not any("SELECT users.id" in sql for sql in statements)


async def test_shared_answer_preserves_reviewed_sibling(client, flow):
    headers, first, adapter = flow
    first_prefix = await prepared(client, headers, first, save=True)
    other = (await client.post("/api/v1/applications", headers={**headers, "Idempotency-Key": "reviewed-sibling"},
        json={"job_id": first["job"]["id"]})).json()["data"]
    prefix = f'/api/v1/applications/{other["id"]}'
    await client.post(prefix + "/start", headers=headers)
    review = await client.post(prefix + "/review", headers=headers)
    assert review.status_code == 200, review.text
    before = review.json()["data"]
    data = (await client.get(first_prefix, headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "authorization")
    result = await client.post(first_prefix + "/answers", headers={**headers, "Idempotency-Key": "shared-after-review"},
        json={"answers": [{"field_id": field["id"], "value": "Updated shared answer"}]})
    assert result.status_code == 200, result.text
    assert (await client.get(prefix, headers=headers)).json()["data"] == before
    assert adapter.submissions == []
    refreshed = await client.post(prefix + "/start", headers=headers)
    assert refreshed.status_code == 200, refreshed.text
    fields = refreshed.json()["data"]["fields"]
    assert next(f for f in fields if f["field_key"] == "authorization")["value"] == "Updated shared answer"
    assert {f["field_key"]: f["id"] for f in fields} == {f["field_key"]: f["id"] for f in before["fields"]}


async def test_concurrent_answer_updates_reject_stale_revision(client, flow):
    import asyncio
    headers, app, _ = flow
    prefix = await prepared(client, headers, app)
    data = (await client.get(prefix, headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "authorization")
    async def save(index):
        return await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": f"concurrent-{index}"},
            json={"expected_revision": data["revision"], "answers": [
                {"field_id": field["id"], "value": str(index), "save_for_reuse": False}]})
    results = await asyncio.gather(save(1), save(2))
    assert sorted(r.status_code for r in results) == [200, 409]
    saved = next(r.json()["data"] for r in results if r.status_code == 200)
    assert (await client.get(prefix, headers=headers)).json()["data"] == saved


@pytest.mark.parametrize("field_key,value", [("authorization", "Fresh shared"), ("name", "Updated Candidate")])
async def test_postgres_shared_save_skips_busy_sibling_and_user_lock(client, flow, database_engine, field_key, value):
    import asyncio
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from app.models.user import User
    if database_engine.dialect.name != "postgresql":
        pytest.skip("Real PostgreSQL row locks required")
    headers, first, _ = flow
    prefix = await prepared(client, headers, first)
    other = (await client.post("/api/v1/applications", headers={**headers, "Idempotency-Key": "busy-sibling"},
        json={"job_id": first["job"]["id"]})).json()["data"]
    sibling = f'/api/v1/applications/{other["id"]}'
    before = (await client.post(sibling + "/start", headers=headers)).json()["data"]
    data = (await client.get(prefix, headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == field_key)
    factory = async_sessionmaker(database_engine, expire_on_commit=False)
    async with factory() as lock:
        app = await lock.get(Application, UUID(first["id"]))
        # Non-key User writes must not block app editing or FK KEY SHARE checks.
        await lock.execute(select(User.id).where(User.id == app.user_id).with_for_update(key_share=True))
        await lock.execute(select(Application.id).where(Application.id == UUID(other["id"])).with_for_update())
        result = await asyncio.wait_for(client.post(prefix + "/answers",
            headers={**headers, "Idempotency-Key": "skip-busy"},
            json={"expected_revision": data["revision"], "answers": [{"field_id": field["id"], "value": value}]}), 3)
        assert result.status_code == 200, result.text
        assert (await client.get(sibling, headers=headers)).json()["data"] == before
        await lock.rollback()
    refreshed = (await client.post(sibling + "/start", headers=headers)).json()["data"]
    assert next(f for f in refreshed["fields"] if f["field_key"] == field_key)["value"] == value


async def test_postgres_answer_save_and_user_serialized_action_do_not_deadlock(client, flow, database_engine, monkeypatch):
    import asyncio
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from app.repositories import applications as repo, matching
    if database_engine.dialect.name != "postgresql":
        pytest.skip("Real PostgreSQL row locks required")
    headers, first, _ = flow
    prefix = await prepared(client, headers, first)
    data = (await client.get(prefix, headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "authorization")
    reserved, proceed = asyncio.Event(), asyncio.Event()
    original = repo.reserve_answer_revision
    async def reserve(session, app, revision):
        result = await original(session, app, revision)
        reserved.set()
        await proceed.wait()
        return result
    monkeypatch.setattr(repo, "reserve_answer_revision", reserve)
    request = asyncio.create_task(client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": "lock-order"},
        json={"answers": [{"field_id": field["id"], "value": "Yes", "save_for_reuse": False}]}))
    waiting = None
    try:
        await asyncio.wait_for(reserved.wait(), 3)
        factory = async_sessionmaker(database_engine, expire_on_commit=False)
        async with factory() as lock:
            app = await lock.get(Application, UUID(first["id"]))
            await matching.lock_user(lock, app.user_id)
            waiting = asyncio.create_task(repo.owned(lock, app.user_id, app.id, lock=True))
            proceed.set()
            response = await asyncio.wait_for(request, 3)
            assert response.status_code == 200, response.text
            assert (await asyncio.wait_for(waiting, 3)).revision == response.json()["data"]["revision"]
            await lock.rollback()
    finally:
        proceed.set()
        for task in [request, waiting]:
            if task and not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
