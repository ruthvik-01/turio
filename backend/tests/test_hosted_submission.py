"""Regression coverage for public form parsing and approved hosted submission."""
import copy
import os

import pytest
from playwright.async_api import async_playwright

from app.adapters import ashby_hosted
from app.core.errors import AppError
from test_applications import FORM, flow


@pytest.mark.skipif(os.environ.get("TURIO_BROWSER_TESTS") != "1", reason="Isolated Chromium fixture.")
async def test_blank_consent_title_uses_public_name_and_preserves_question():
    async with async_playwright() as driver:
        browser = await driver.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.set_content('<div data-field-path=consent><label></label><p>May we contact you for one year?</p>'
                                   '<label><input type=checkbox>I agree</label></div>')
            page._turio_hosted_form = {"sections": [{"fieldEntries": [{"field": {
                "path": "consent", "title": "", "humanReadablePath": "Future Contact Consent", "type": "MultiValueSelect",
                "selectableValues": [{"value": "data_consent_ack", "label": "I agree"}]},
                "descriptionHtml": "<p>May we contact you for one year?</p>", "isRequired": False}]}]}
            result = await ashby_hosted.schema(page)
            assert result["fields"][0]["label"] == "Future Contact Consent"
            assert result["fields"][0]["help_text"] == "May we contact you for one year?"
            assert not await page.locator("input").is_checked()
        finally:
            await browser.close()


@pytest.mark.skipif(os.environ.get("TURIO_BROWSER_TESTS") != "1", reason="Isolated Chromium fixture.")
async def test_required_boolean_question_can_be_answered_no():
    async with async_playwright() as driver:
        browser = await driver.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.set_content('<div data-field-path=relationship><label>Do you have relatives here?</label><input type=checkbox></div>')
            page._turio_hosted_form = {"sections": [{"fieldEntries": [{"field": {
                "path": "relationship", "title": "Do you have relatives here?", "type": "Boolean"}, "isRequired": True}]}]}
            schema = await ashby_hosted.schema(page)
            field = schema["fields"][0]
            assert field["input_type"] == "select"
            assert field["options"] == [{"value": "true", "label": "Yes"}, {"value": "false", "label": "No"}]
            await ashby_hosted.fill(page, {"schema": schema, "resume_id": None, "answers": {"relationship": "false"}}, None)
            assert not await page.locator("input").is_checked()
        finally:
            await browser.close()


async def test_supported_hosted_snapshot_uses_existing_approval_boundary(client, flow):
    headers, app, adapter = flow
    schema = copy.deepcopy(FORM)
    schema.update(version="ashby-hosted-v1", manual_submission_required=False, submission_transport="ashby-hosted-v2", schema_contract_version="stable-actions-v1")
    schema["fields"] = schema["fields"][:2]

    async def inspect(url):
        return copy.deepcopy(schema)

    adapter.inspect = inspect
    prefix = f"/api/v1/applications/{app['id']}"
    assert (await client.post(prefix + "/start", headers=headers)).status_code == 200
    data = (await client.post(prefix + "/review", headers=headers)).json()["data"]
    assert data["manual_submission_required"] is False
    rejected = await client.post(prefix + "/approve-submit", headers={**headers, "Idempotency-Key": "no-consent"},
                                 json={"approved": False, "review_token": data["review_token"]})
    assert rejected.status_code == 422 and not adapter.submissions
    submitted = await client.post(prefix + "/approve-submit", headers={**headers, "Idempotency-Key": "hosted-approved"},
                                  json={"approved": True, "review_token": data["review_token"]})
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["data"]["status"] == "submitted"
    replay = await client.post(prefix + "/approve-submit", headers={**headers, "Idempotency-Key": "hosted-approved"},
                               json={"approved": True, "review_token": data["review_token"]})
    assert replay.json()["data"] == submitted.json()["data"] and len(adapter.submissions) == 1


@pytest.mark.skipif(os.environ.get("TURIO_BROWSER_TESTS") != "1", reason="Isolated Chromium fixture.")
async def test_action_nonces_do_not_change_review_hash_but_action_meaning_does():
    async with async_playwright() as driver:
        browser = await driver.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.set_content('<div data-field-path=name><label>Name</label><input></div>')
            metadata = {"_turio_form_controls": [{"definition_id": "definition", "controls": [{"identifier": "first-nonce", "title": "Submit"}]}],
                        "sections": [{"fieldEntries": [{"field": {"path": "name", "type": "String", "title": "Name"}, "isRequired": True}]}]}
            page._turio_hosted_form = metadata
            first = await ashby_hosted.schema(page)
            metadata["_turio_form_controls"][0]["controls"][0]["identifier"] = "second-nonce"
            assert await ashby_hosted.schema(page) == first
            metadata["_turio_form_controls"][0]["controls"][0]["title"] = "Different action"
            assert await ashby_hosted.schema(page) != first
        finally:
            await browser.close()


async def test_old_transitional_hosted_snapshot_requires_fresh_preparation(client, flow):
    headers, app, adapter = flow
    schema = copy.deepcopy(FORM)
    schema.update(version="ashby-hosted-v1", manual_submission_required=False, submission_transport="ashby-hosted-v2")
    schema["fields"] = schema["fields"][:2]
    async def inspect(url):
        return copy.deepcopy(schema)
    adapter.inspect = inspect
    prefix = f"/api/v1/applications/{app['id']}"
    assert (await client.post(prefix + "/start", headers=headers)).status_code == 200
    data = (await client.post(prefix + "/review", headers=headers)).json()["data"]
    response = await client.post(prefix + "/approve-submit", headers={**headers, "Idempotency-Key": "old-unstable-schema"},
                                json={"approved": True, "review_token": data["review_token"]})
    assert response.status_code == 422 and not adapter.submissions


async def test_confirmed_removed_posting_disappears_but_history_survives(client, flow):
    headers, app, adapter = flow
    adapter.error = AppError("JOB_UNAVAILABLE", "The employer has removed this posting.", 404)
    response = await client.post(f"/api/v1/applications/{app['id']}/start", headers=headers)
    assert response.status_code == 404
    assert (await client.get("/api/v1/jobs", headers=headers)).json()["data"]["total"] == 0
    assert (await client.get(f"/api/v1/jobs/{app['job']['id']}", headers=headers)).status_code == 404
    assert (await client.get(f"/api/v1/applications/{app['id']}", headers=headers)).status_code == 200


async def test_temporary_inspection_failure_keeps_job_visible(client, flow):
    headers, app, adapter = flow
    adapter.error = AppError("BROWSER_ACTION_FAILED", "Temporary network failure.", 503)
    assert (await client.post(f"/api/v1/applications/{app['id']}/start", headers=headers)).status_code == 503
    assert (await client.get("/api/v1/jobs", headers=headers)).json()["data"]["total"] == 1


def test_hosted_rpc_permit_binds_exact_reviewed_body_and_cannot_replay():
    import json
    from types import SimpleNamespace
    from app.adapters.hosted_submission import JsonPermit

    body = {"operationName": "ApiSetFormValue", "query": "mutation Fixture { apply }",
            "variables": {"path": "name", "value": "Reviewed Candidate"}}
    request = SimpleNamespace(method="POST", url="https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiSetFormValue",
                              headers={"content-type": "application/json"}, post_data_buffer=json.dumps(body).encode())
    permit = JsonPermit(request.url, body)
    assert permit.allow(request)
    assert not permit.allow(request)
    altered = copy.deepcopy(body)
    altered["variables"]["value"] = "Unreviewed Candidate"
    request.post_data_buffer = json.dumps(altered).encode()
    assert not JsonPermit(request.url, body).allow(request)
    request.post_data_buffer = b'{"operationName":"bad","operationName":"ApiSetFormValue"}'
    assert not JsonPermit(request.url, body).allow(request)
    body["variables"]["value"] = False
    altered = copy.deepcopy(body)
    altered["variables"]["value"] = 0
    request.post_data_buffer = json.dumps(altered).encode()
    assert not JsonPermit(request.url, body).allow(request)


def test_final_permit_binds_posting_forms_and_rejects_duplicate_submission():
    import json
    from types import SimpleNamespace
    from app.adapters.hosted_submission import FinalPermit, QUERIES

    forms = [{"id": "render", "sourceFormDefinitionId": "definition", "formControls": [{"identifier": "submit"}]}]
    variables = {"organizationHostedJobsPageName": "fixture", "jobPostingId": "job",
                 "formRenderIdentifier": "render", "formDefinitionIdentifier": "definition",
                 "actionIdentifier": "submit", "recaptchaToken": "fixture-site-token",
                 "sourceAttributionCode": None, "viewedAutomatedProcessingLegalNoticeRuleId": None,
                 "deviceFingerprint": None, "applicationRequestId": None}
    body = {"operationName": "ApiSubmitSingleApplicationFormAction", "query": QUERIES["ApiSubmitSingleApplicationFormAction"],
            "variables": variables}
    request = SimpleNamespace(method="POST", url="https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiSubmitSingleApplicationFormAction",
                              headers={"content-type": "application/json"}, post_data_buffer=json.dumps(body).encode())
    permit = FinalPermit("https://jobs.ashbyhq.com/fixture/job/application", forms)
    assert permit.allow(request)
    assert not permit.allow(request)
    variables["jobPostingId"] = "another-job"
    request.post_data_buffer = json.dumps(body).encode()
    assert not FinalPermit("https://jobs.ashbyhq.com/fixture/job/application", forms).allow(request)


def test_normal_posting_submit_can_omit_undefined_optional_variables():
    import json
    from types import SimpleNamespace
    from app.adapters.hosted_submission import FinalPermit, QUERIES

    forms = [{"id": "render", "sourceFormDefinitionId": "definition", "formControls": [{"identifier": "submit"}]}]
    body = {"operationName": "ApiSubmitSingleApplicationFormAction", "query": QUERIES["ApiSubmitSingleApplicationFormAction"],
            "variables": {"organizationHostedJobsPageName": "fixture", "jobPostingId": "job", "formRenderIdentifier": "render",
                          "formDefinitionIdentifier": "definition", "actionIdentifier": "submit", "recaptchaToken": "site-token"}}
    request = SimpleNamespace(method="POST", url="https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiSubmitSingleApplicationFormAction",
                              headers={"content-type": "application/json"}, post_data_buffer=json.dumps(body).encode())
    assert FinalPermit("https://jobs.ashbyhq.com/fixture/job/application", forms).allow(request)


def test_final_state_audit_rejects_later_answer_changes_and_unapproved_defaults():
    from app.adapters.hosted_submission import audit_forms

    original = [{"id": "render", "sections": [{"fieldEntries": [
        {"field": {"path": "name", "type": "String"}, "fieldValue": {"value": None}},
        {"field": {"path": "consent", "type": "Boolean"}, "fieldValue": {"value": False}}]}]}]
    current = copy.deepcopy(original)
    current[0]["sections"][0]["fieldEntries"][0]["fieldValue"]["value"] = "Reviewed"
    audit_forms(original, current, {"name": {"value": "Reviewed"}})
    current[0]["sections"][0]["fieldEntries"][0]["fieldValue"]["value"] = "Unreviewed"
    with pytest.raises(AppError):
        audit_forms(original, current, {"name": {"value": "Reviewed"}})
    current[0]["sections"][0]["fieldEntries"][0]["fieldValue"]["value"] = "Reviewed"
    current[0]["sections"][0]["fieldEntries"][1]["fieldValue"]["value"] = True
    with pytest.raises(AppError):
        audit_forms(original, current, {"name": {"value": "Reviewed"}})
    original[0]["sections"][0]["fieldEntries"][1]["fieldValue"]["value"] = None
    current[0]["sections"][0]["fieldEntries"][1]["fieldValue"]["value"] = False
    with pytest.raises(AppError):
        audit_forms(original, current, {"name": {"value": "Reviewed"}})


def test_integral_number_echo_matches_without_accepting_boolean_substitution():
    from app.adapters.hosted_submission import audit_forms

    original = [{"id": "render", "sections": [{"fieldEntries": [
        {"field": {"path": "years", "type": "Number"}, "fieldValue": {"value": None}}]}]}]
    current = copy.deepcopy(original)
    current[0]["sections"][0]["fieldEntries"][0]["fieldValue"]["value"] = 1
    audit_forms(original, current, {"years": {"value": 1.0}})
    current[0]["sections"][0]["fieldEntries"][0]["fieldValue"]["value"] = True
    with pytest.raises(AppError):
        audit_forms(original, current, {"years": {"value": 1.0}})


async def test_csv_refresh_does_not_reopen_confirmed_closed_posting(client, flow, session, tmp_path):
    from app.services.job_ingestion import ingest_dataset
    from support import job_row, write_jobs_csv

    headers, app, adapter = flow
    adapter.error = AppError("JOB_UNAVAILABLE", "Confirmed removed posting.", 404)
    assert (await client.post(f"/api/v1/applications/{app['id']}/start", headers=headers)).status_code == 404
    await ingest_dataset(session, path=str(write_jobs_csv(tmp_path / "updated.csv", [job_row(description="Changed source copy.")])))
    assert (await client.get("/api/v1/jobs", headers=headers)).json()["data"]["total"] == 0


async def test_hosted_required_multiselect_accepts_only_reviewed_available_choices(client, flow):
    headers, app, adapter = flow
    schema = copy.deepcopy(FORM)
    schema["fields"] = schema["fields"][:2] + [{"field_key": "segments", "label": "What segments have you worked with?",
        "input_type": "multiselect", "required": True, "source_locator": "#segments", "options": [
            {"value": "SMB", "label": "SMB"}, {"value": "Enterprise", "label": "Enterprise"}]}]

    async def inspect(url):
        return copy.deepcopy(schema)

    adapter.inspect = inspect
    prefix = f"/api/v1/applications/{app['id']}"
    data = (await client.post(prefix + "/start", headers=headers)).json()["data"]
    field = next(f for f in data["fields"] if f["field_key"] == "segments")
    response = await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": "multi-answer"},
                                json={"answers": [{"field_id": field["id"], "value": ["SMB", "Enterprise"], "user_confirmed": True}]})
    assert response.status_code == 200, response.text
    assert response.json()["data"]["missing_fields"] == []
    assert next(f for f in response.json()["data"]["fields"] if f["field_key"] == "segments")["value"] == ["SMB", "Enterprise"]
    for index, invalid in enumerate([["Unknown"], ["SMB", "SMB"], "SMB"]):
        rejected = await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": f"bad-multi-{index}"},
                                     json={"answers": [{"field_id": field["id"], "value": invalid, "user_confirmed": True}]})
        assert rejected.status_code == 422


def test_upload_destination_is_restricted_to_verified_s3_urls():
    from app.adapters.hosted_submission import trusted_upload

    assert trusted_upload("https://fixture.s3.us-east-1.amazonaws.com/")
    for url in ["http://fixture.s3.amazonaws.com/", "https://s3.amazonaws.com.evil.invalid/",
                "https://user@fixture.s3.amazonaws.com/", "https://127.0.0.1/upload", "https://fixture.s3.amazonaws.com:8443/"]:
        assert not trusted_upload(url)
