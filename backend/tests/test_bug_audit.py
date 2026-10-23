"""Regressions for the 2026-10-14 usability audit; no employer requests."""
import copy

import pytest

from app.services.form_mapping import intent
from app.services.resume_parser import parse_resume
from test_applications import FORM, flow, prepared


@pytest.mark.parametrize("label,want", [
    ("Link to LinkedIn profile", "linkedin_url"), ("LinkedIn page", "linkedin_url"),
    ("Please share your GitHub profile link", "github_url"),
    ("How many LinkedIn followers do you have?", "custom"),
    ("Do you consent to sharing your LinkedIn profile?", "custom"),
])
def test_contact_question_intents(label, want):
    assert intent(label, "text") == want


@pytest.mark.parametrize("text,want", [
    ("linkedin.com/in/sample", "https://linkedin.com/in/sample"),
    ("linkedin.com/sample", "https://www.linkedin.com/in/sample"),
    ("LinkedIn: sample-name", "https://www.linkedin.com/in/sample-name"),
    ("linkedin.com/company/example", None),
])
def test_linkedin_resume_formats(text, want):
    assert parse_resume("Synthetic Candidate\n" + text).linkedin_url == want


async def test_saved_contact_updates_profile_and_other_wordings(client, flow):
    headers, app, adapter = flow
    form = copy.deepcopy(FORM)
    form["fields"].append(dict(field_key="linkedin", label="LinkedIn", input_type="url",
        required=True, source_locator="#linkedin", options=[]))
    async def inspect(url): return copy.deepcopy(form)
    adapter.inspect = inspect
    prefix = f"/api/v1/applications/{app['id']}"
    data = (await client.post(prefix + "/start", headers=headers)).json()["data"]
    before = (await client.get("/api/v1/profiles/me", headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "linkedin")
    response = await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": "contact-sync"},
        json={"answers": [dict(field_id=field["id"], value="https://linkedin.com/in/saved")]})
    assert response.status_code == 200, response.text
    profile = (await client.get("/api/v1/profiles/me", headers=headers)).json()["data"]
    assert profile["linkedin_url"] == "https://linkedin.com/in/saved"
    assert profile["version"] == before["version"] + 1
    form["fields"][-1]["label"] = "Link to LinkedIn profile"
    data = (await client.post(prefix + "/start", headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "linkedin")
    assert field["value"] == profile["linkedin_url"] and field["user_confirmed"]


async def test_profile_override_is_application_only_and_survives_prepare(client, flow):
    headers, app, _ = flow
    prefix = await prepared(client, headers, app)
    data = (await client.get(prefix, headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "name")
    response = await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": "override"},
        json={"answers": [dict(field_id=field["id"], value="Application Name", save_for_reuse=False)]})
    assert response.status_code == 200, response.text
    assert (await client.get("/api/v1/profiles/me", headers=headers)).json()["data"]["full_name"] == "Candidate One"
    data = (await client.post(prefix + "/start", headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "name")
    assert field["value"] == "Application Name" and field["value_source"] == "application_only"
    assert (await client.post(prefix + "/review", headers=headers)).status_code == 200


async def test_uncertain_reset_requires_explicit_employer_check(client, flow):
    headers, app, adapter = flow
    prefix = await prepared(client, headers, app)
    token = (await client.post(prefix + "/review", headers=headers)).json()["data"]["review_token"]
    adapter.verified = False
    response = await client.post(prefix + "/approve-submit", headers={**headers, "Idempotency-Key": "uncertain"},
        json=dict(review_token=token, approved=True))
    assert response.json()["data"]["status"] == "verification_failed"
    assert (await client.patch(prefix, headers=headers, json=dict(reset_to_review=True))).status_code == 422
    response = await client.patch(prefix, headers=headers, json=dict(reset_to_review=True, confirmed_not_submitted=True))
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["status"] == "ready_for_review" and data["review_token"] is None
    assert len(adapter.submissions) == 1
    assert (await client.post(prefix + "/approve-submit", headers={**headers, "Idempotency-Key": "stale"},
        json=dict(review_token=token, approved=True))).status_code == 409


async def test_reusable_profile_correction_can_review_without_reprepare(client, flow):
    headers, app, _ = flow
    prefix = await prepared(client, headers, app)
    data = (await client.get(prefix, headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "name")
    response = await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": "global-correction"},
        json={"answers": [dict(field_id=field["id"], value="Corrected Name", save_for_reuse=True)]})
    assert response.status_code == 200, response.text
    profile = (await client.get("/api/v1/profiles/me", headers=headers)).json()["data"]
    assert profile["full_name"] == "Corrected Name"
    assert response.json()["data"]["profile_version"] == profile["version"]
    assert (await client.post(prefix + "/review", headers=headers)).status_code == 200


async def test_profile_sync_rejects_overlong_value_without_partial_save(client, flow):
    headers, app, _ = flow
    prefix = await prepared(client, headers, app)
    field = next(f for f in (await client.get(prefix, headers=headers)).json()["data"]["fields"] if f["field_key"] == "name")
    response = await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": "invalid-contact"},
        json={"answers": [dict(field_id=field["id"], value="x" * 256)]})
    assert response.status_code == 422
    assert (await client.get("/api/v1/profiles/me", headers=headers)).json()["data"]["full_name"] == "Candidate One"
    field = next(f for f in (await client.get(prefix, headers=headers)).json()["data"]["fields"] if f["field_key"] == "name")
    assert field["value"] == "Candidate One"


async def test_local_override_does_not_replace_sibling_profile_field(client, flow):
    headers, app, adapter = flow
    form = copy.deepcopy(FORM)
    form["fields"].append(dict(field_key="legal-name", label="Legal name", input_type="text",
        required=True, source_locator="#legal-name", options=[]))
    async def inspect(url): return copy.deepcopy(form)
    adapter.inspect = inspect
    prefix = await prepared(client, headers, app)
    field = next(f for f in (await client.get(prefix, headers=headers)).json()["data"]["fields"] if f["field_key"] == "name")
    response = await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": "one-name-only"},
        json={"answers": [dict(field_id=field["id"], value="Preferred Name", save_for_reuse=False)]})
    assert response.status_code == 200, response.text
    data = (await client.post(prefix + "/start", headers=headers)).json()["data"]
    values = {f["field_key"]: f["value"] for f in data["fields"]}
    assert values["name"] == "Preferred Name"
    assert values["legal-name"] == "Candidate One"
