"""Optional questions cannot block review; salary prompts explain their units."""
import copy

import pytest

from test_applications import FORM, flow, prepared


async def test_unconfirmed_optional_suggestion_does_not_block_or_enter_review(client, flow):
    headers, app, adapter = flow
    form = copy.deepcopy(FORM)
    form["version"] = "ashby-hosted-v1"
    form["fields"].append({"field_key": "background", "label": "Tell us about your background",
        "input_type": "textarea", "required": False, "source_locator": "#background", "options": []})
    async def inspect(url): return form
    adapter.inspect = inspect
    prefix = await prepared(client, headers, app)
    data = (await client.get(prefix, headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "background")
    draft = await client.post(prefix + f"/fields/{field['id']}/draft", headers=headers)
    assert draft.status_code == 200, draft.text
    reviewed = await client.post(prefix + "/review", headers=headers)
    assert reviewed.status_code == 200, reviewed.text
    snapshots = []
    async def handoff(url, snapshot): snapshots.append(snapshot)
    adapter.handoff = handoff
    data = reviewed.json()["data"]
    response = await client.post(prefix + "/handoff", headers={**headers, "Idempotency-Key": "optional-skipped"},
        json={"approved": True, "review_token": data["review_token"]})
    assert response.status_code == 200, response.text
    assert "background" not in snapshots[0]["answers"]


async def test_unconfirmed_optional_ai_does_not_block_required_answer_save(client, session, flow):
    from uuid import UUID
    from app.models.application import ApplicationAnswer
    headers, app, adapter = flow
    form = copy.deepcopy(FORM)
    form["fields"].append({"field_key": "optional", "label": "Optional personal site", "input_type": "text",
        "required": False, "source_locator": "#optional", "options": []})
    async def inspect(url): return form
    adapter.inspect = inspect
    prefix = f"/api/v1/applications/{app['id']}"
    data = (await client.post(prefix + "/start", headers=headers)).json()["data"]
    optional = next(f for f in data["fields"] if f["field_key"] == "optional")
    session.add(ApplicationAnswer(field_id=UUID(optional["id"]), value="Unconfirmed legacy suggestion",
        value_source="ai_profile", user_confirmed=False))
    await session.commit()
    required = next(f for f in data["fields"] if f["field_key"] == "authorization")
    saved = await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": "required-only"},
        json={"answers": [{"field_id": required["id"], "value": "Yes"}]})
    assert saved.status_code == 200, saved.text
    assert (await client.post(prefix + "/review", headers=headers)).status_code == 200


@pytest.mark.parametrize("label, input_type, hint, expected", [
    ("Expectation Salary per annum", "text", None, ["not specified", "annual", "USD", "INR"]),
    ("Expected salary (INR per month)", "text", None, ["INR", "Indian rupees", "monthly"]),
    ("Expected salary", "number", "Annual amount in USD, numbers only", ["USD", "US dollars", "annual", "numbers only"]),
])
async def test_salary_field_exposes_currency_period_and_format(client, flow, label, input_type, hint, expected):
    headers, app, adapter = flow
    form = copy.deepcopy(FORM)
    form["fields"].append({"field_key": "salary", "label": label, "input_type": input_type,
        "required": True, "source_locator": "#salary", "options": [], "help_text": hint})
    async def inspect(url): return form
    adapter.inspect = inspect
    response = await client.post(f"/api/v1/applications/{app['id']}/start", headers=headers)
    assert response.status_code == 200, response.text
    field = next(f for f in response.json()["data"]["fields"] if f["field_key"] == "salary")
    help_text = field.get("help_text") or ""
    for text in expected:
        assert text.casefold() in help_text.casefold()
