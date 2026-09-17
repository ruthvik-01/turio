"""Approval safety and application API integration with an explicit fake adapter."""

import copy

import pytest

from app.api.v1.applications import get_adapter
from app.core.errors import AppError
from app.services.job_ingestion import ingest_dataset
from support import auth_headers, job_row, write_jobs_csv

FORM = {"version": "fixture-v1", "submit_locator": "#submit", "fields": [
    {"field_key": "name", "label": "Full name", "input_type": "text", "required": True, "source_locator": "#name", "options": []},
    {"field_key": "email", "label": "Email", "input_type": "email", "required": True, "source_locator": "#email", "options": []},
    {"field_key": "authorization", "label": "Are you legally authorized to work in this country?", "input_type": "text", "required": True, "source_locator": "#authorization", "options": []},
]}


class FakeAdapter:
    def __init__(self):
        self.submissions = []
        self.fills = []
        self.verified = True
        self.error = None

    def check_url(self, url):
        pass

    async def inspect(self, url):
        if self.error:
            raise self.error
        return copy.deepcopy(FORM)

    async def fill(self, url, snapshot):
        self.fills.append(copy.deepcopy(snapshot))

    async def submit(self, url, snapshot):
        self.submissions.append(copy.deepcopy(snapshot))
        return {"verified": self.verified, "fixture": True}


@pytest.fixture
async def flow(client, session, tmp_path):
    headers = await auth_headers(client)
    await client.patch("/api/v1/profiles/me", headers=headers,
                       json={"full_name": "Candidate One", "location": "London", "skills": ["Python"]})
    path = write_jobs_csv(tmp_path / "applications.csv", [job_row()])
    await ingest_dataset(session, path=str(path))
    jobs = (await client.get("/api/v1/jobs", headers=headers)).json()["data"]["jobs"]
    adapter = FakeAdapter()
    client._transport.app.dependency_overrides[get_adapter] = lambda: adapter
    response = await client.post("/api/v1/applications", headers={**headers, "Idempotency-Key": "create-1"},
                                 json={"job_id": jobs[0]["id"]})
    assert response.status_code == 201, response.text
    app = response.json()["data"]
    return headers, app, adapter


async def prepared(client, headers, app, *, confirmed=True, save=False):
    prefix = f"/api/v1/applications/{app['id']}"
    start = await client.post(prefix + "/start", headers=headers)
    assert start.status_code == 200, start.text
    field = next(f for f in start.json()["data"]["fields"] if f["field_key"] == "authorization")
    response = await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": "answer"},
        json={"answers": [{"field_id": field["id"], "value": "Yes", "user_confirmed": confirmed, "save_for_reuse": save}]})
    assert response.status_code == 200, response.text
    return prefix


async def test_create_replay_and_conflicting_key(client, flow):
    headers, app, _ = flow
    request = {"job_id": app["job"]["id"]}
    repeated = await client.post("/api/v1/applications", headers={**headers, "Idempotency-Key": "create-1"}, json=request)
    assert repeated.json()["data"] == app
    conflict = await client.post("/api/v1/applications", headers={**headers, "Idempotency-Key": "create-1"},
                                json={**request, "resume_id": app["id"]})
    assert conflict.status_code == 409
    assert (await client.get("/api/v1/applications", headers=headers)).json()["data"]["total"] == 1


async def test_mapping_reuses_known_data_never_infers_authorization(client, flow):
    headers, app, adapter = flow
    response = await client.post(f"/api/v1/applications/{app['id']}/start", headers=headers)
    data = response.json()["data"]
    fields = {f["field_key"]: f for f in data["fields"]}
    assert fields["name"]["value"] == "Candidate One"
    assert fields["email"]["value"] == "candidate@example.com"
    assert fields["authorization"]["value"] is None
    assert data["status"] == "needs_input"
    assert adapter.submissions == []


async def test_resume_uploaded_after_draft_is_reused_without_new_application(client, flow, make_pdf, monkeypatch):
    from support import RESUME_TEXT, upload_resume
    headers, app, adapter = flow
    assert app["resume_id"] is None
    uploaded = await upload_resume(client, headers, make_pdf(RESUME_TEXT))
    assert uploaded.status_code == 201
    resume_id = uploaded.json()["data"]["resume"]["id"]
    form = copy.deepcopy(FORM)
    form["fields"].append({"field_key": "resume", "label": "Upload Résumé / CV",
                          "input_type": "file", "required": True, "source_locator": "#resume", "options": []})
    monkeypatch.setattr("test_applications.FORM", form)
    prefix = f"/api/v1/applications/{app['id']}"
    started = await client.post(prefix + "/start", headers=headers)
    assert started.status_code == 200, started.text
    data = started.json()["data"]
    assert data["resume_id"] == resume_id
    field = next(f for f in data["fields"] if f["field_key"] == "resume")
    assert field["value"] == resume_id and field["value_source"] == "profile"
    assert field["user_confirmed"] and "Upload Résumé / CV" not in data["missing_fields"]
    assert not adapter.submissions
    again = await client.post("/api/v1/applications", headers={**headers, "Idempotency-Key": "second-job"},
                              json={"job_id": app["job"]["id"]})
    assert again.json()["data"]["resume_id"] == resume_id
    review = await client.post(f"/api/v1/applications/{app['id']}/review", headers=headers)
    assert review.status_code == 422


async def test_phase5_reuses_one_resume_and_reviewed_profile_across_jobs(
    client, flow, session, tmp_path, make_pdf, storage, monkeypatch
):
    """Isolated synthetic API verification, not human benchmark evidence."""
    import hashlib
    from support import RESUME_TEXT, upload_resume

    headers, app, adapter = flow
    pdf = make_pdf(RESUME_TEXT)
    upload = await upload_resume(client, headers, pdf)
    assert upload.status_code == 201, upload.text
    resume = upload.json()["data"]["resume"]
    assert resume["checksum"] == hashlib.sha256(pdf).hexdigest()
    updated = await client.patch("/api/v1/profiles/me", headers=headers,
                                 json={"full_name": "Reviewed Fixture Name", "location": "Fixture City"})
    assert updated.status_code == 200
    schema = copy.deepcopy(FORM)
    schema["fields"].extend([
        {"field_key": "resume", "label": "Resume", "input_type": "file",
         "required": True, "source_locator": "#resume", "options": []},
        {"field_key": "location", "label": "Current city", "input_type": "text",
         "required": True, "source_locator": "#location", "options": []},
    ])
    monkeypatch.setattr("test_applications.FORM", schema)
    other = write_jobs_csv(tmp_path / "second-job.csv", [job_row(ats_id="phase5-second-job")])
    await ingest_dataset(session, path=str(other))
    matches = await client.post("/api/v1/matches", headers=headers, json={"method": "keyword"})
    assert matches.status_code == 200, matches.text
    matched_jobs = {m["job"]["id"]: m["job"] for m in matches.json()["data"]["matches"]}
    assert app["job"]["id"] in matched_jobs
    other_id = next(id for id in matched_jobs if id != app["job"]["id"])

    prefix = f"/api/v1/applications/{app['id']}"
    initial = await client.post(prefix + "/start", headers=headers)
    assert initial.status_code == 200, initial.text
    data = initial.json()["data"]
    assert data["status"] == "needs_input" and data["review_token"] is None
    assert data["missing_fields"] == [FORM["fields"][2]["label"]]
    authorization = next(f for f in data["fields"] if f["field_key"] == "authorization")
    answered = await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": "phase5-answer"},
        json={"answers": [{"field_id": authorization["id"], "value": "No",
                           "user_confirmed": True, "save_for_reuse": True}]})
    assert answered.status_code == 200 and answered.json()["data"]["status"] == "ready_for_review"
    created = await client.post("/api/v1/applications", headers={**headers, "Idempotency-Key": "phase5-other"},
                                json={"job_id": other_id})
    assert created.status_code == 201, created.text
    second = created.json()["data"]

    for application in [app, second]:
        route = f"/api/v1/applications/{application['id']}"
        started = await client.post(route + "/start", headers=headers)
        assert started.status_code == 200, started.text
        prepared_data = started.json()["data"]
        assert prepared_data["job"] == matched_jobs[application["job"]["id"]]
        assert prepared_data["missing_fields"] == []
        values = {f["field_key"]: f for f in prepared_data["fields"]}
        for key, expected in [("name", "Reviewed Fixture Name"), ("location", "Fixture City"),
                              ("resume", resume["id"])]:
            assert values[key]["value"] == expected
            assert values[key]["value_source"] == "profile" and values[key]["user_confirmed"]
        assert values["authorization"]["value"] == "No"
        review = await client.post(route + "/review", headers=headers)
        assert review.status_code == 200, review.text
        reviewed = review.json()["data"]
        assert reviewed["review_token"] and reviewed["submitted_at"] is None
        assert adapter.fills[-1]["resume_id"] == resume["id"]
        assert adapter.fills[-1]["answers"]["resume"] == resume["id"]
        assert adapter.fills[-1]["answers"]["name"] == "Reviewed Fixture Name"
        assert adapter.submissions == []
        assert not any(e["event_type"] == "submission_started" for e in reviewed["events"])
    assert len(storage.put_calls) == 1
    assert list(storage.objects.values()) == [pdf]


async def test_review_does_not_submit_and_approval_is_exactly_once(client, flow):
    headers, app, adapter = flow
    prefix = await prepared(client, headers, app)
    review = await client.post(prefix + "/review", headers=headers)
    assert review.status_code == 200, review.text
    token = review.json()["data"]["review_token"]
    assert token and not adapter.submissions
    request = {"review_token": token, "approved": True}
    approved_headers = {**headers, "Idempotency-Key": "approval"}
    result = await client.post(prefix + "/approve-submit", headers=approved_headers, json=request)
    assert result.json()["data"]["status"] == "submitted"
    assert adapter.submissions == adapter.fills
    repeat = await client.post(prefix + "/approve-submit", headers=approved_headers, json=request)
    assert repeat.json()["data"] == result.json()["data"]
    assert len(adapter.submissions) == 1
    again = await client.post(prefix + "/approve-submit", headers={**headers, "Idempotency-Key": "another"}, json=request)
    assert again.status_code == 409


@pytest.mark.parametrize("stage", ["created", "needs_input", "reviewed"])
async def test_cancellation_blocks_preparation_review_and_stale_approval(client, flow, stage):
    headers, app, adapter = flow
    prefix = f"/api/v1/applications/{app['id']}"
    token = "0" * 64
    if stage == "needs_input":
        assert (await client.post(prefix + "/start", headers=headers)).status_code == 200
    elif stage == "reviewed":
        await prepared(client, headers, app)
        review = await client.post(prefix + "/review", headers=headers)
        assert review.status_code == 200
        token = review.json()["data"]["review_token"]
    cancelled = await client.patch(prefix, headers=headers, json={"cancel": True})
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["status"] == "cancelled"
    assert cancelled.json()["data"]["review_token"] is None
    for action in ["/start", "/review"]:
        assert (await client.post(prefix + action, headers=headers)).status_code == 409
    approval = await client.post(prefix + "/approve-submit",
        headers={**headers, "Idempotency-Key": "cancelled-approval"},
        json={"approved": True, "review_token": token})
    assert approval.status_code == 409
    assert adapter.submissions == []


async def test_unreviewed_and_explicitly_unapproved_requests_cannot_submit(client, flow):
    headers, app, adapter = flow
    prefix = f"/api/v1/applications/{app['id']}"
    result = await client.post(prefix + "/approve-submit",
        headers={**headers, "Idempotency-Key": "before-review"},
        json={"approved": True, "review_token": "0" * 64})
    assert result.status_code == 409
    await prepared(client, headers, app)
    reviewed = await client.post(prefix + "/review", headers=headers)
    token = reviewed.json()["data"]["review_token"]
    rejected = await client.post(prefix + "/approve-submit",
        headers={**headers, "Idempotency-Key": "not-approved"},
        json={"approved": False, "review_token": token})
    assert rejected.status_code == 422
    assert adapter.submissions == []


async def test_stale_profile_review_and_draft_answers_cannot_submit(client, flow):
    headers, app, adapter = flow
    prefix = await prepared(client, headers, app, confirmed=False)
    assert (await client.post(prefix + "/review", headers=headers)).status_code == 422
    detail = (await client.get(prefix, headers=headers)).json()["data"]
    field = next(f for f in detail["fields"] if f["field_key"] == "authorization")
    await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": "confirm"},
                     json={"answers": [{"field_id": field["id"], "value": "Yes"}]})
    review = (await client.post(prefix + "/review", headers=headers)).json()["data"]
    await client.patch("/api/v1/profiles/me", headers=headers, json={"location": "Paris"})
    result = await client.post(prefix + "/approve-submit", headers={**headers, "Idempotency-Key": "stale"},
                              json={"approved": True, "review_token": review["review_token"]})
    assert result.status_code == 409
    assert adapter.submissions == []
    repeated = (await client.post(prefix + "/start", headers=headers)).json()["data"]
    assert next(f for f in repeated["fields"] if f["field_key"] == "authorization")["value"] == "Yes"


async def test_uncertain_submission_is_never_retried(client, flow):
    headers, app, adapter = flow
    adapter.verified = False
    prefix = await prepared(client, headers, app)
    review = (await client.post(prefix + "/review", headers=headers)).json()["data"]
    request = {"approved": True, "review_token": review["review_token"]}
    result = await client.post(prefix + "/approve-submit", headers={**headers, "Idempotency-Key": "uncertain"}, json=request)
    assert result.json()["data"]["status"] == "verification_failed"
    assert result.json()["data"]["submitted_at"] is None
    await client.post(prefix + "/approve-submit", headers={**headers, "Idempotency-Key": "uncertain"}, json=request)
    assert len(adapter.submissions) == 1


async def test_saved_answer_reused_only_when_explicitly_requested(client, flow):
    headers, app, _ = flow
    await prepared(client, headers, app, save=True)
    new = (await client.post("/api/v1/applications", headers={**headers, "Idempotency-Key": "create-2"},
                            json={"job_id": app["job"]["id"]})).json()["data"]
    data = (await client.post(f"/api/v1/applications/{new['id']}/start", headers=headers)).json()["data"]
    assert data["missing_fields"] == []
    assert next(f for f in data["fields"] if f["field_key"] == "authorization")["value_source"] == "saved_answer"


async def test_owner_isolation_and_required_idempotency(client, flow):
    headers, app, _ = flow
    prefix = f"/api/v1/applications/{app['id']}"
    other = await auth_headers(client, "other@example.com")
    assert (await client.get(prefix, headers=other)).status_code == 404
    assert (await client.post(prefix + "/start", headers=other)).status_code == 404
    assert (await client.get(prefix)).status_code == 401
    assert (await client.post("/api/v1/applications", headers=headers, json={"job_id": app["job"]["id"]})).status_code == 422
    assert (await client.get("/api/v1/applications", headers=other)).json()["data"]["total"] == 0


async def test_manual_tracking_is_distinct_and_filterable(client, flow):
    headers, app, adapter = flow
    prefix = f"/api/v1/applications/{app['id']}"
    result = await client.patch(prefix, headers=headers, json={"submitted_manually": True, "outcome": "interview", "notes": "Follow up Friday"})
    assert result.json()["data"]["submission_method"] == "manual"
    assert result.json()["data"]["status"] == "submitted"
    assert adapter.submissions == []
    assert (await client.get("/api/v1/applications?outcome=interview&limit=1", headers=headers)).json()["data"]["total"] == 1
    assert (await client.get("/api/v1/applications?outcome=offer", headers=headers)).json()["data"]["total"] == 0


async def test_inspection_failure_is_recorded_without_fake_success(client, flow):
    headers, app, adapter = flow
    adapter.error = AppError("BROWSER_ACTION_FAILED", "Fixture failure.", 503)
    prefix = f"/api/v1/applications/{app['id']}"
    assert (await client.post(prefix + "/start", headers=headers)).status_code == 503
    result = (await client.get(prefix, headers=headers)).json()["data"]
    assert result["status"] == "automation_failed"
    assert any(e["event_type"] == "automation_failed" for e in result["events"])


async def test_unexpected_submit_failure_is_recorded_without_sensitive_details(client, flow):
    headers, app, adapter = flow
    prefix = await prepared(client, headers, app)
    review = (await client.post(prefix + "/review", headers=headers)).json()["data"]

    async def crash(url, snapshot):
        raise RuntimeError("sensitive-provider-response")

    adapter.submit = crash
    result = await client.post(prefix + "/approve-submit", headers={**headers, "Idempotency-Key": "crash"},
                               json={"approved": True, "review_token": review["review_token"]})
    assert result.status_code == 200
    assert result.json()["data"]["status"] == "verification_failed"
    assert "sensitive-provider-response" not in result.text


async def test_summary_is_owner_scoped(client, flow):
    headers, _, _ = flow
    result = (await client.get("/api/v1/applications/summary", headers=headers)).json()["data"]
    assert result["total"] == 1 and result["in_progress"] == 1
    assert len(result["days"]) == 28 and sum(d["count"] for d in result["days"]) == 1
    other = await auth_headers(client, "empty-summary@example.com")
    assert (await client.get("/api/v1/applications/summary", headers=other)).json()["data"]["total"] == 0


async def test_factual_draft_requires_confirmation_and_does_not_answer_sensitive_questions(client, flow):
    headers, app, adapter = flow
    schema = copy.deepcopy(FORM)
    schema["fields"].append({"field_key": "background", "label": "Describe your relevant experience",
        "input_type": "textarea", "required": False, "source_locator": "#background", "options": []})

    async def inspect(url):
        return schema

    adapter.inspect = inspect
    prefix = await prepared(client, headers, app)
    fields = (await client.get(prefix, headers=headers)).json()["data"]["fields"]
    narrative = next(f for f in fields if f["field_key"] == "background")
    response = await client.post(prefix + f"/fields/{narrative['id']}/draft", headers=headers)
    assert response.status_code == 200, response.text
    draft = next(f for f in response.json()["data"]["fields"] if f["id"] == narrative["id"])
    assert draft["value_source"] == "draft" and draft["user_confirmed"] is False
    assert draft["value"] == "My profile lists skills in Python."
    assert (await client.post(prefix + "/review", headers=headers)).status_code == 422
    sensitive = next(f for f in fields if f["field_key"] == "authorization")
    assert (await client.post(prefix + f"/fields/{sensitive['id']}/draft", headers=headers)).status_code == 422
