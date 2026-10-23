"""Hosted preparation and manual handoff; no employer submissions."""
import copy
import io
import json

import pytest

from app.adapters.ashby import AshbyAdapter
from app.core.config import get_settings
from app.core.errors import AppError
from test_applications import FORM, flow


def test_ashby_posting_outside_original_trial_is_eligible(monkeypatch):
    monkeypatch.setattr(get_settings(), "browser_automation_enabled", True)
    AshbyAdapter(None).check_url("https://jobs.ashbyhq.com/0x/c6510c38-a082-4d6b-8872-4645071543f3/application")


@pytest.mark.parametrize("url", [
    "http://jobs.ashbyhq.com/0x/job/application",
    "https://jobs.ashbyhq.com.evil.invalid/0x/job/application",
    "https://user@jobs.ashbyhq.com/0x/job/application",
    "https://jobs.ashbyhq.com:8443/0x/job/application",
    "https://jobs.ashbyhq.com/",
    "https://jobs.ashbyhq.com/../job/application",
])
def test_ashby_url_boundary_remains_restricted(monkeypatch, url):
    monkeypatch.setattr(get_settings(), "browser_automation_enabled", True)
    with pytest.raises(AppError):
        AshbyAdapter(None).check_url(url)


async def hosted_review(client, flow):
    headers, app, adapter = flow
    schema = copy.deepcopy(FORM)
    schema["version"] = "ashby-hosted-v1"
    schema["fields"] = schema["fields"][:2]

    async def inspect(url):
        return copy.deepcopy(schema)

    adapter.inspect = inspect
    prefix = f"/api/v1/applications/{app['id']}"
    assert (await client.post(prefix + "/start", headers=headers)).status_code == 200
    result = await client.post(prefix + "/review", headers=headers)
    assert result.status_code == 200, result.text
    return headers, prefix, adapter, result.json()["data"]


async def test_hosted_review_does_not_send_values_before_handoff_approval(client, flow):
    _, _, adapter, data = await hosted_review(client, flow)
    assert data["manual_submission_required"] is True
    assert data["review_token"]
    assert adapter.fills == [] and adapter.submissions == []


async def test_hosted_automatic_submission_is_rejected(client, flow):
    headers, prefix, adapter, data = await hosted_review(client, flow)
    response = await client.post(prefix + "/approve-submit", headers={**headers, "Idempotency-Key": "no-auto"},
        json={"approved": True, "review_token": data["review_token"]})
    assert response.status_code == 422
    assert adapter.submissions == []


async def test_handoff_requires_current_review_and_never_marks_submitted(client, flow):
    headers, prefix, adapter, data = await hosted_review(client, flow)
    handoffs = []

    async def handoff(url, snapshot):
        handoffs.append(copy.deepcopy(snapshot))

    adapter.handoff = handoff
    payload = {"approved": True, "review_token": data["review_token"]}
    assert (await client.post(prefix + "/handoff", headers={"Idempotency-Key": "unauthenticated"}, json=payload)).status_code == 401
    from support import auth_headers
    other = await auth_headers(client, "other-handoff@example.com")
    assert (await client.post(prefix + "/handoff", headers={**other, "Idempotency-Key": "other-owner"}, json=payload)).status_code == 404
    assert (await client.post(prefix + "/handoff", headers={**headers, "Idempotency-Key": "unapproved"},
        json={**payload, "approved": False})).status_code == 422
    assert (await client.post(prefix + "/handoff", headers={**headers, "Idempotency-Key": "stale"},
        json={**payload, "review_token": "0" * 64})).status_code == 409
    request_headers = {**headers, "Idempotency-Key": "manual-handoff"}
    response = await client.post(prefix + "/handoff", headers=request_headers, json=payload)
    assert response.status_code == 200, response.text
    result = response.json()["data"]
    assert result["status"] == "ready_for_review" and result["submitted_at"] is None
    assert result["submission_method"] is None and result["review_token"] is None
    assert any(event["event_type"] == "manual_handoff_ready" for event in result["events"])
    assert len(handoffs) == 1 and handoffs[0]["answers"]["name"] == "Candidate One"
    repeated = await client.post(prefix + "/handoff", headers=request_headers, json=payload)
    assert repeated.json()["data"] == result and len(handoffs) == 1
    assert adapter.submissions == []


async def test_failed_handoff_remains_unsubmitted_and_replay_does_not_reopen(client, flow):
    headers, prefix, adapter, data = await hosted_review(client, flow)
    async def handoff(url, snapshot):
        raise AppError("BROWSER_ACTION_FAILED", "Synthetic browser startup failure", 503)
    adapter.handoff = handoff
    payload = {"approved": True, "review_token": data["review_token"]}
    headers = {**headers, "Idempotency-Key": "failed-handoff"}
    response = await client.post(prefix + "/handoff", headers=headers, json=payload)
    assert response.status_code == 200, response.text
    result = response.json()["data"]
    assert result["status"] == "automation_failed" and result["submitted_at"] is None
    assert result["review_token"] is None and result["operation_kind"] is None
    assert (await client.post(prefix + "/handoff", headers=headers, json=payload)).json()["data"] == result
    assert adapter.submissions == []


async def test_browser_bootstrap_rechecks_authorization_before_releasing_values(monkeypatch):
    from app.adapters import ashby
    monkeypatch.setattr(get_settings(), "browser_automation_enabled", True)
    class Input(io.BytesIO):
        saved = b""
        def close(self):
            self.saved = self.getvalue()
            super().close()
    class Process:
        def __init__(self):
            self.stdin = Input()
            self.stdout = io.BytesIO(b'{"inspected":true}\n{"ready":true}\n')
            self.killed = False
        def kill(self):
            self.killed = True
        def wait(self):
            return 0
    process = Process()
    monkeypatch.setattr(ashby.subprocess, "Popen", lambda *args, **kwargs: process)
    calls = []
    async def authorize(snapshot):
        calls.append(snapshot)
        if len(calls) == 2:
            raise AppError("SUBMISSION_NOT_APPROVED", "Profile changed during bootstrap", 409)
    adapter = AshbyAdapter(None)
    adapter.authorize_handoff = authorize
    snapshot = {"schema": {"version": "ashby-hosted-v1", "fields": []}, "answers": {}, "resume_id": None}
    with pytest.raises(AppError, match="changed"):
        await adapter.handoff("https://jobs.ashbyhq.com/0x/fixture/application", snapshot)
    assert len(calls) == 2 and process.killed
    lines = process.stdin.saved.splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["snapshot"] == snapshot
