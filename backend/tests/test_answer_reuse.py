"""Known facts and authored answers survive subsequent applications."""

import copy

import pytest

from app.services.form_mapping import intent
from app.services.resume_parser import parse_resume
from test_applications import FORM, flow
from support import auth_headers


async def test_answer_saved_once_updates_pending_drafts_and_preserves_review(client, flow):
    headers, first, adapter = flow
    ids = [first['id']]
    for index in range(3):
        app = (await client.post('/api/v1/applications', headers={**headers, 'Idempotency-Key': f'pending-{index}'},
                                json={'job_id': first['job']['id']})).json()['data']
        ids.append(app['id'])
    prepared = [(await client.post(f'/api/v1/applications/{app_id}/start', headers=headers)).json()['data'] for app_id in ids]
    second = prepared[1]
    field = next(f for f in second['fields'] if f['field_key'] == 'authorization')
    await client.post(f"/api/v1/applications/{second['id']}/answers", headers={**headers, 'Idempotency-Key': 'older-local'},
                     json={'answers': [{'field_id': field['id'], 'value': 'Old shared answer'}]})
    reviewed = (await client.post(f"/api/v1/applications/{second['id']}/review", headers=headers)).json()['data']
    assert reviewed['review_token']
    fills_before_save = len(adapter.fills)
    field = next(f for f in prepared[0]['fields'] if f['field_key'] == 'authorization')
    response = await client.post(f"/api/v1/applications/{first['id']}/answers", headers={**headers, 'Idempotency-Key': 'answer-once'},
                                 json={'answers': [{'field_id': field['id'], 'value': 'Updated confirmed answer'}]})
    assert response.status_code == 200, response.text
    for app_id in ids:
        data = (await client.get(f'/api/v1/applications/{app_id}', headers=headers)).json()['data']
        if app_id == second['id']:
            assert data == reviewed
            continue
        shared = next(f for f in data['fields'] if f['field_key'] == 'authorization')
        assert shared['value'] == 'Updated confirmed answer' and shared['user_confirmed']
        assert data['status'] == 'ready_for_review' and not data['missing_fields']
        assert data['review_token'] is None
    assert len(adapter.fills) == fills_before_save and adapter.submissions == []


async def test_shared_answer_does_not_replace_application_only_or_terminal_answers(client, flow):
    headers, first, _ = flow
    apps = []
    for index in range(2):
        app = (await client.post('/api/v1/applications', headers={**headers, 'Idempotency-Key': f'protected-{index}'},
                                json={'job_id': first['job']['id']})).json()['data']
        app = (await client.post(f"/api/v1/applications/{app['id']}/start", headers=headers)).json()['data']
        field = next(f for f in app['fields'] if f['field_key'] == 'authorization')
        await client.post(f"/api/v1/applications/{app['id']}/answers", headers={**headers, 'Idempotency-Key': f'local-{index}'},
                         json={'answers': [{'field_id': field['id'], 'value': 'Application-specific', 'save_for_reuse': False}]})
        apps.append(app)
    await client.patch(f"/api/v1/applications/{apps[1]['id']}", headers=headers, json={'cancel': True})
    data = (await client.post(f"/api/v1/applications/{first['id']}/start", headers=headers)).json()['data']
    field = next(f for f in data['fields'] if f['field_key'] == 'authorization')
    await client.post(f"/api/v1/applications/{first['id']}/answers", headers={**headers, 'Idempotency-Key': 'new-shared'},
                     json={'answers': [{'field_id': field['id'], 'value': 'Shared answer'}]})
    for app in apps:
        data = (await client.get(f"/api/v1/applications/{app['id']}", headers=headers)).json()['data']
        assert next(f for f in data['fields'] if f['field_key'] == 'authorization')['value'] == 'Application-specific'


@pytest.mark.parametrize("label, expected", [
    ("Please share your LinkedIn profile URL", "linkedin_url"),
    ("What is your phone number?", "phone"),
    ("Please provide your GitHub profile URL (optional)", "github_url"),
    ("Enter your full name", "full_name"),
    ("Please share your work authorization status", "custom"),
    ("LinkedIn profile of someone who referred you", "custom"),
])
def test_fact_labels_without_sensitive_keyword_guessing(label, expected):
    assert intent(label, "text") == expected


def test_bare_resume_contact_urls_are_reusable():
    parsed = parse_resume("Synthetic Candidate\nlinkedin.com/in/synthetic-candidate\ngithub.com/synthetic-candidate")
    assert parsed.linkedin_url == "https://linkedin.com/in/synthetic-candidate"
    assert parsed.github_url == "https://github.com/synthetic-candidate"


async def test_resume_link_fills_long_employer_label(client, flow, make_pdf):
    headers, app, adapter = flow
    uploaded = await client.post("/api/v1/resumes", headers=headers,
        files={"file": ("synthetic.pdf", make_pdf("Synthetic Candidate\nhttps://linkedin.com/in/synthetic"), "application/pdf")})
    assert uploaded.status_code == 201, uploaded.text
    form = copy.deepcopy(FORM)
    form["fields"].append({"field_key": "linkedin", "label": "Please share your LinkedIn profile URL",
        "input_type": "url", "required": True, "source_locator": "#linkedin", "options": []})
    async def inspect(url): return form
    adapter.inspect = inspect
    data = (await client.post(f"/api/v1/applications/{app['id']}/start", headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "linkedin")
    assert field["value"] == "https://linkedin.com/in/synthetic"
    assert field["user_confirmed"] and field["value_source"] == "profile"
    assert field["label"] not in data["missing_fields"]


async def test_typed_answer_is_saved_by_default_and_reused_across_fact_labels(client, flow):
    headers, app, adapter = flow
    form = copy.deepcopy(FORM)
    form["fields"][2].update(field_key="phone", label="Please share your phone number", input_type="tel")
    async def inspect(url): return copy.deepcopy(form)
    adapter.inspect = inspect
    prefix = f"/api/v1/applications/{app['id']}"
    data = (await client.post(prefix + "/start", headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "phone")
    response = await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": "authored"},
        json={"answers": [{"field_id": field["id"], "value": "+1 555 0100"}]})
    assert response.status_code == 200, response.text
    form["fields"][2].update(label="Phone", input_type="text")
    created = await client.post("/api/v1/applications", headers={**headers, "Idempotency-Key": "next-app"},
        json={"job_id": app["job"]["id"]})
    next_id = created.json()["data"]["id"]
    data = (await client.post(f"/api/v1/applications/{next_id}/start", headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "phone")
    assert field["value"] == "+1 555 0100" and field["user_confirmed"]
    assert data["missing_fields"] == []
    assert adapter.fills == [] and adapter.submissions == []


async def test_bulk_create_reuses_owned_application_without_duplicates(client, flow):
    from test_applications import prepared
    headers, app, _ = flow
    prefix = await prepared(client, headers, app)
    review = await client.post(prefix + "/review", headers=headers)
    assert review.status_code == 200, review.text
    token = review.json()["data"]["review_token"]
    response = await client.post("/api/v1/applications", headers={**headers, "Idempotency-Key": "bulk-reuse"},
        json={"job_id": app["job"]["id"], "reuse_existing": True})
    assert response.status_code == 201, response.text
    assert response.json()["data"]["id"] == app["id"]
    assert response.json()["data"]["review_token"] == token
    assert (await client.get("/api/v1/applications", headers=headers)).json()["data"]["total"] == 1
    other = await auth_headers(client, "bulk-other@example.com")
    response = await client.post("/api/v1/applications", headers={**other, "Idempotency-Key": "other-bulk"},
        json={"job_id": app["job"]["id"], "reuse_existing": True})
    assert response.json()["data"]["id"] != app["id"]


async def test_stored_resume_fact_fills_missing_profile_without_reupload(client, flow, make_pdf):
    headers, app, adapter = flow
    uploaded = await client.post("/api/v1/resumes", headers=headers,
        files={"file": ("stored.pdf", make_pdf("Synthetic Candidate\nhttps://linkedin.com/in/stored"), "application/pdf")})
    assert uploaded.status_code == 201
    await client.patch("/api/v1/profiles/me", headers=headers, json={"linkedin_url": None})
    form = copy.deepcopy(FORM)
    form["fields"].append({"field_key": "linkedin", "label": "LinkedIn", "input_type": "url",
        "required": True, "source_locator": "#linkedin", "options": []})
    async def inspect(url): return form
    adapter.inspect = inspect
    data = (await client.post(f"/api/v1/applications/{app['id']}/start", headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "linkedin")
    assert field["value"] == "https://linkedin.com/in/stored" and field["user_confirmed"]
    assert (await client.get("/api/v1/profiles/me", headers=headers)).json()["data"]["linkedin_url"] is None


async def test_preexisting_confirmed_answers_are_reused_without_saved_answer_row(client, session, flow):
    from app.models.application import ApplicationAnswer
    headers, app, _ = flow
    prefix = f"/api/v1/applications/{app['id']}"
    data = (await client.post(prefix + "/start", headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "authorization")
    # Simulate an authored answer stored by the previous release, before reuse defaulted on.
    from uuid import UUID
    session.add(ApplicationAnswer(field_id=UUID(field["id"]), value="Historical confirmed answer",
        value_source="user", user_confirmed=True))
    await session.commit()
    created = (await client.post("/api/v1/applications", headers={**headers, "Idempotency-Key": "history-app"},
        json={"job_id": app["job"]["id"]})).json()["data"]
    data = (await client.post(f"/api/v1/applications/{created['id']}/start", headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "authorization")
    assert field["value"] == "Historical confirmed answer" and field["user_confirmed"]


async def test_saved_contact_correction_wins_over_older_resume(client, session, flow, make_pdf):
    from types import SimpleNamespace
    from uuid import UUID
    from app.models.application import SavedAnswer
    from app.services.form_mapping import question_key
    headers, app, adapter = flow
    response = await client.post("/api/v1/resumes", headers=headers,
        files={"file": ("older.pdf", make_pdf("Synthetic Candidate\nhttps://linkedin.com/in/older"), "application/pdf")})
    assert response.status_code == 201
    await client.patch("/api/v1/profiles/me", headers=headers, json={"linkedin_url": None})
    form = copy.deepcopy(FORM)
    field = {"field_key": "linkedin", "label": "LinkedIn", "input_type": "url",
        "required": True, "source_locator": "#linkedin", "options": []}
    form["fields"].append(field)
    async def inspect(url): return form
    adapter.inspect = inspect
    user = (await client.get("/api/v1/auth/me", headers=headers)).json()["data"]
    session.add(SavedAnswer(user_id=UUID(user["id"]), question_key=question_key(SimpleNamespace(**field)),
        value="https://linkedin.com/in/corrected"))
    await session.commit()
    data = (await client.post(f"/api/v1/applications/{app['id']}/start", headers=headers)).json()["data"]
    value = next(f for f in data["fields"] if f["field_key"] == "linkedin")
    assert value["value"] == "https://linkedin.com/in/corrected" and value["value_source"] == "saved_answer"


@pytest.mark.parametrize("flags", [{"user_confirmed": False}, {"save_for_reuse": False}])
async def test_unconfirmed_or_application_only_answers_do_not_reappear(client, flow, flags):
    headers, app, _ = flow
    prefix = f"/api/v1/applications/{app['id']}"
    data = (await client.post(prefix + "/start", headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "authorization")
    response = await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": "not-reusable"},
        json={"answers": [{"field_id": field["id"], "value": "Local or unconfirmed answer", **flags}]})
    assert response.status_code == 200
    created = (await client.post("/api/v1/applications", headers={**headers, "Idempotency-Key": "no-reuse-app"},
        json={"job_id": app["job"]["id"]})).json()["data"]
    data = (await client.post(f"/api/v1/applications/{created['id']}/start", headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "authorization")
    assert field["value"] is None


async def test_legacy_saved_contact_key_remains_readable(client, session, flow):
    from types import SimpleNamespace
    from uuid import UUID
    from app.models.application import SavedAnswer
    from app.services.form_mapping import legacy_question_key
    headers, app, adapter = flow
    form = copy.deepcopy(FORM)
    field = {"field_key": "phone", "label": "Phone", "input_type": "tel", "required": True,
             "source_locator": "#phone", "options": []}
    form["fields"].append(field)
    async def inspect(url): return form
    adapter.inspect = inspect
    user = (await client.get("/api/v1/auth/me", headers=headers)).json()["data"]
    session.add(SavedAnswer(user_id=UUID(user["id"]), question_key=legacy_question_key(SimpleNamespace(**field)), value="555-0110"))
    await session.commit()
    data = (await client.post(f"/api/v1/applications/{app['id']}/start", headers=headers)).json()["data"]
    value = next(f for f in data["fields"] if f["field_key"] == "phone")
    assert value["value"] == "555-0110" and value["user_confirmed"]


@pytest.mark.parametrize("originally_required", [True, False])
async def test_required_form_consent_is_not_reused_for_another_application(client, flow, originally_required):
    headers, app, adapter = flow
    form = copy.deepcopy(FORM)
    form["fields"][2].update(field_key="consent", label="I agree to these application terms", input_type="checkbox", required=originally_required)
    async def inspect(url): return form
    adapter.inspect = inspect
    prefix = f"/api/v1/applications/{app['id']}"
    data = (await client.post(prefix + "/start", headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "consent")
    response = await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": "form-consent"},
        json={"answers": [{"field_id": field["id"], "value": True}]})
    assert response.status_code == 200
    form["fields"][2]["required"] = True
    created = (await client.post("/api/v1/applications", headers={**headers, "Idempotency-Key": "new-consent-app"},
        json={"job_id": app["job"]["id"]})).json()["data"]
    data = (await client.post(f"/api/v1/applications/{created['id']}/start", headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "consent")
    assert field["value"] is None and not field["user_confirmed"]
