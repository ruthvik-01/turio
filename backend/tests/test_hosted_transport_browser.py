"""Real browser/production network guard; all employer traffic ends in fixtures."""
import copy
import json
import os

import pytest

from app.adapters.ashby_queries import PUBLIC_QUERIES
from app.adapters.hosted_submission import QUERIES
from app.adapters.native_submission import FileProof, parse_native_body
from app.core.errors import AppError
from test_browser_adapter import site, FORM_URL, ORIGINAL_PDF

pytestmark = pytest.mark.skipif(os.environ.get("TURIO_BROWSER_TESTS") != "1", reason="Isolated Chromium transport fixture.")


class HostedSite:
    def __init__(self, native, mode="success", surveys=False):
        self.native, self.mode, self.surveys = native, mode, surveys
        self.calls, self.final_calls, self.uploads = [], [], []
        self.counter = 0
        self.forms = []

    def form(self, identifier, fields, definition):
        return {"id": identifier, "sourceFormDefinitionId": definition,
                "formControls": [{"identifier": "submit", "title": "Submit"}],
                "sections": [{"fieldEntries": [{"field": {"path": key, "type": kind, "title": title, "isMany": False,
                    "selectableValues": choices, "locationTypes": ["City", "Country"] if kind == "Location" else None},
                    "isRequired": required, "fieldValue": {"value": None}}
                    for key, kind, title, required, choices in fields]}]}

    def reset(self):
        self.counter += 1
        self.forms = [self.form(f"render-{self.counter}", [
            ("name", "String", "Full name", True, []), ("email", "Email", "Email", True, []),
            ("resume", "File", "Resume", True, []), ("relationship", "Boolean", "Do you have relatives here?", True, []),
            ("segments", "MultiValueSelect", "Segments", True, [{"value": "SMB", "label": "SMB"}, {"value": "Enterprise", "label": "Enterprise"}]),
            ("location", "Location", "Location", True, []), ("consent", "Boolean", "Future contact", False, [])], "main-definition")]
        if self.surveys:
            self.forms.append(self.form(f"survey-{self.counter}", [("survey", "Boolean", "Survey", False, [])], "survey-definition"))

    def html(self):
        public = {"operationName": "ApiJobPosting", "query": PUBLIC_QUERIES["ApiJobPosting"],
                  "variables": {"organizationHostedJobsPageName": "1password", "jobPostingId": "turio-local-fixture"}}
        fields = '<div data-field-path=name><label>Full name</label><input></div>' \
                 '<div data-field-path=email><label>Email</label><input type=email></div>' \
                 '<div data-field-path=resume><label>Resume</label><input type=file></div>' \
                 '<div data-field-path=relationship><label>Do you have relatives here?</label><input type=checkbox></div>' \
                 '<div data-field-path=segments><label>Segments</label><input type=checkbox><input type=checkbox></div>' \
                 '<div data-field-path=location><label>Location</label><input role=combobox></div>' \
                 '<div data-field-path=consent><label>Future contact</label><input type=checkbox></div>'
        if self.surveys:
            fields += '<div data-field-path=survey><label>Survey</label><input type=checkbox></div>'
        operation = "ApiSubmitMultipleFormsAction" if self.surveys else "ApiSubmitSingleApplicationFormAction"
        return fields + '<button class=ashby-application-form-submit-button onclick="submitFixture()">Submit Application</button><script>' + f"""
          fetch('/api/non-user-graphql?op=ApiJobPosting',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:{json.dumps(json.dumps(public))}}})
            .then(r=>r.json()).then(r=>window.posting=r.data.jobPosting);
          async function submitFixture() {{
            const main=window.posting.applicationForm;
            const variables={{organizationHostedJobsPageName:'1password',jobPostingId:'turio-local-fixture',recaptchaToken:'site-generated-fixture-token'}};
            if ({json.dumps(self.surveys)}) Object.assign(variables,{{applicationFormRenderIdentifier:main.id,applicationFormDefinitionIdentifier:main.sourceFormDefinitionId,
              applicationFormActionIdentifier:main.formControls[0].identifier,surveyIdentifiers:window.posting.surveyForms.map(f=>({{formRenderId:f.id,sourceFormDefinitionId:f.sourceFormDefinitionId,actionIdentifier:f.formControls[0].identifier}}))}});
            else Object.assign(variables,{{formRenderIdentifier:main.id,formDefinitionIdentifier:main.sourceFormDefinitionId,actionIdentifier:main.formControls[0].identifier}});
            await fetch('/api/non-user-graphql?op={operation}',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{operationName:{json.dumps(operation)},query:{json.dumps(QUERIES[operation])},variables}})}});
          }}
        </script>"""

    async def route(self, route):
        request = route.request
        if request.url == FORM_URL and request.method == "GET":
            await route.fulfill(content_type="text/html", body=self.html())
            return
        if request.url == "https://fixture.s3.amazonaws.com/" and request.method == "POST":
            fields, files = parse_native_body(request.headers["content-type"], request.post_data_buffer)
            assert fields == {"Content-Type": "application/pdf", "key": "approved.pdf", "policy": "fixture-policy"}
            assert files == {"file": FileProof.from_bytes("original.pdf", ORIGINAL_PDF)}
            self.uploads.append(files)
            await route.fulfill(status=204, headers={"access-control-allow-origin": "*"})
            return
        if request.method != "POST" or "/api/non-user-graphql?op=" not in request.url:
            raise AssertionError("Unexpected request escaped production guard")
        body = request.post_data_json
        operation, variables = body["operationName"], body["variables"]
        if operation == "ApiJobPosting":
            self.reset()
            posting = None if self.mode == "removed" else {"applicationForm": self.forms[0], "surveyForms": self.forms[1:]}
            await route.fulfill(json={"data": {"jobPosting": posting}})
            return
        self.calls.append((operation, copy.deepcopy(variables)))
        if operation == "ApiCreateFileUploadHandle":
            assert variables["contentLength"] == len(ORIGINAL_PDF)
            data = {"fileUploadHandle": {"handle": "uploaded-handle", "url": "https://fixture.s3.amazonaws.com/",
                                       "fields": {"key": "approved.pdf", "policy": "fixture-policy"}}}
        elif operation == "ApiAutocompleteGeoLocation":
            data = {"result": {"suggestions": [{"name": "London, United Kingdom", "geoLocationPath": [{"providerLocationId": "london"}]}]}}
        elif operation in {"ApiSetFormValue", "ApiSetFormValueToFile"}:
            form = next(f for f in self.forms if f["id"] == variables["formRenderIdentifier"])
            entries = form["sections"][0]["fieldEntries"]
            entry = next(e for e in entries if e["field"]["path"] == variables["path"])
            if operation == "ApiSetFormValueToFile":
                assert self.uploads and variables["fileHandle"] == "uploaded-handle"
                entry["fieldValue"] = {"id": "original-file-id", "filename": "original.pdf"}
            else:
                entry["fieldValue"] = {"value": variables["value"]}
                if self.mode == "overwrite" and variables["path"] == "email":
                    entries[0]["fieldValue"] = {"value": "Unreviewed replacement"}
            data = {"setFormValueToFile" if operation == "ApiSetFormValueToFile" else "setFormValue": copy.deepcopy(form)}
        else:
            assert operation in {"ApiSubmitSingleApplicationFormAction", "ApiSubmitMultipleFormsAction"}
            self.final_calls.append(body)
            receipt = {"__typename": "FormSubmitSuccess" if self.mode != "rejected" else "FormRender"}
            result = {"applicationFormResult": receipt, "messages": {"blockMessageForCandidateHtml": None}}
            if self.surveys:
                result["surveyFormResults"] = [receipt]
            data = {"submitMultipleFormsAction" if self.surveys else "submitApplicationFormAction": result}
        await route.fulfill(json={"data": data})

    async def prepared(self):
        self.native.route = self.route
        adapter = self.native.adapter()
        schema = await adapter.inspect(FORM_URL)
        assert schema["manual_submission_required"] is False
        return adapter, {"schema": schema, "resume_id": "owned-resume", "profile_version": 1, "revision": 1, "url": FORM_URL,
                         "answers": {"name": "Reviewed Candidate", "email": "reviewed@example.invalid", "resume": "owned-resume",
                                     "relationship": "false", "segments": ["SMB", "Enterprise"], "location": "London, United Kingdom"}}


@pytest.mark.parametrize("surveys", [False, True])
async def test_approved_hosted_transport_sends_original_file_and_verifies_employer_receipt(site, surveys):
    fixture = HostedSite(site, surveys=surveys)
    adapter, snapshot = await fixture.prepared()
    result = await adapter.submit(FORM_URL, snapshot)
    assert result["verified"] is True
    assert len(fixture.final_calls) == 1 and len(fixture.uploads) == 1
    entries = fixture.forms[0]["sections"][0]["fieldEntries"]
    values = {e["field"]["path"]: e["fieldValue"] for e in entries}
    assert values["name"]["value"] == "Reviewed Candidate"
    assert values["relationship"]["value"] is False
    assert values["segments"]["value"] == ["SMB", "Enterprise"]
    assert values["location"]["value"] == {"text": "London, United Kingdom", "providerLocationId": "london"}
    assert values["consent"]["value"] is None


async def test_later_server_answer_change_stops_before_final_submit(site):
    fixture = HostedSite(site, mode="overwrite")
    adapter, snapshot = await fixture.prepared()
    with pytest.raises(AppError, match="changed after verification"):
        await adapter.submit(FORM_URL, snapshot)
    assert fixture.final_calls == []


async def test_http200_without_form_submit_success_is_not_reported_submitted(site):
    fixture = HostedSite(site, mode="rejected")
    adapter, snapshot = await fixture.prepared()
    with pytest.raises(AppError, match="did not confirm"):
        await adapter.submit(FORM_URL, snapshot)
    assert len(fixture.final_calls) == 1


async def test_public_removed_posting_is_identified_without_waiting_for_submit_button(site):
    fixture = HostedSite(site, mode="removed")
    site.route = fixture.route
    with pytest.raises(AppError) as error:
        await site.adapter().inspect(FORM_URL)
    assert error.value.code == "JOB_UNAVAILABLE"
    assert not fixture.calls and not fixture.final_calls


async def test_blocked_later_rpc_does_not_invalidate_accepted_form_update(site):
    from app.adapters.hosted_submission import rpc
    fixture = HostedSite(site)
    site.route = fixture.route
    adapter = site.adapter()
    async with adapter.page(FORM_URL) as (page, gate):
        await adapter.schema(page)
        form = page._turio_hosted_forms[0]
        await page.evaluate("""() => {
          const original = window.fetch.bind(window);
          window.fetch = async (url, options) => {
            const response = await original(url, options);
            if (String(url).includes('op=ApiSetFormValue') && !window.turioNoiseSent) {
              window.turioNoiseSent = true;
              const body = JSON.parse(options.body);
              body.variables.value = 'Unapproved extra answer';
              await original(url, {...options, body:JSON.stringify(body)}).catch(() => {});
            }
            return response;
          };
        }""")
        async def authorize(): pass
        data = await rpc(page, gate, authorize, "ApiSetFormValue", dict(
            organizationHostedJobsPageName="1password", formRenderIdentifier=form["id"],
            formDefinitionIdentifier=form["sourceFormDefinitionId"], path="name", value="Reviewed Candidate"))
        assert data["setFormValue"]["sections"][0]["fieldEntries"][0]["fieldValue"]["value"] == "Reviewed Candidate"
        assert len(fixture.calls) == 1
        assert not fixture.final_calls and not fixture.uploads
