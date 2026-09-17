"""Verify the opt-in UI fixture cannot silently act as a live adapter."""
import runpy
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from support import RESUME_TEXT, auth_headers, upload_resume

SERVER = Path(__file__).with_name("ui_server.py")


def test_ui_server_refuses_unflagged_start(monkeypatch):
    monkeypatch.delenv("TURIO_UI_TEST", raising=False)
    with pytest.raises(RuntimeError, match="Do not deploy"):
        runpy.run_path(str(SERVER))


async def test_ui_fixture_preparation_requires_explicit_approval(monkeypatch, make_pdf):
    monkeypatch.setenv("TURIO_UI_TEST", "1")
    monkeypatch.setenv("TURIO_UI_APPLICATION_FIXTURE", "1")
    fixture = runpy.run_path(str(SERVER))
    app = fixture["app"]
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            sentinel = (await client.get("/api/v1/health/fixture")).json()
            assert sentinel["fixture"] == "turio-disposable-ui"
            assert sentinel["application_fixture"] and sentinel["submissions"] == 0
            headers = await auth_headers(client)
            uploaded = await upload_resume(client, headers, make_pdf(RESUME_TEXT))
            assert uploaded.status_code == 201
            jobs = (await client.get("/api/v1/jobs", headers=headers)).json()["data"]["jobs"]
            created = await client.post("/api/v1/applications",
                headers={**headers, "Idempotency-Key": "ui-create"}, json={"job_id": jobs[0]["id"]})
            assert created.status_code == 201
            prefix = f"/api/v1/applications/{created.json()['data']['id']}"
            started = await client.post(prefix + "/start", headers=headers)
            assert started.status_code == 200
            data = started.json()["data"]
            field = next(f for f in data["fields"] if f["field_key"] == "authorization")
            assert field["value"] is None
            answered = await client.post(prefix + "/answers",
                headers={**headers, "Idempotency-Key": "ui-answer"},
                json={"answers": [{"field_id": field["id"], "value": "No", "user_confirmed": True}]})
            assert answered.status_code == 200
            reviewed = await client.post(prefix + "/review", headers=headers)
            assert reviewed.status_code == 200
            before = (await client.get("/api/v1/health/fixture")).json()
            assert before["resume_writes"] == 1 and before["resume_reads"] == 1
            assert before["submissions"] == 0
            submitted = await client.post(prefix + "/approve-submit",
                headers={**headers, "Idempotency-Key": "ui-approve"},
                json={"approved": True, "review_token": reviewed.json()["data"]["review_token"]})
            assert submitted.status_code == 200
            assert submitted.json()["data"]["status"] == "submitted"
            assert (await client.get("/api/v1/health/fixture")).json()["submissions"] == 1
