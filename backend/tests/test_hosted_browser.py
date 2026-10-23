"""Actual Chromium hosted DOM fixtures. Requests never reach an employer."""
import copy
import os
import asyncio
import json
import sys
from pathlib import Path

import pytest
from playwright.async_api import async_playwright

from app.adapters import ashby_hosted
from app.adapters.ashby_queries import PUBLIC_QUERIES
from app.core.errors import AppError

URL = "https://jobs.ashbyhq.com/0x/fixture/application"
HTML = """<meta charset=utf-8>
<div data-field-path=name><label>Name</label><input id=name></div>
<div data-field-path=email><label>Email</label><input id=email type=email></div>
<div data-field-path=resume><label>Resume</label><input id=resume type=file></div>
<div data-field-path=location><label>Location</label><input role=combobox></div>
<div data-field-path=background><label>Background</label><textarea id=background></textarea></div>
<div data-field-path=choice><label>Choice</label><label><input type=radio name=choice value=yes>Yes</label><label><input type=radio name=choice value=no>No</label></div>
<button class=ashby-application-form-submit-button onclick="window.submitted=true">Submit Application</button>"""
METADATA = {"id": "fixture-form", "sections": [{"fieldEntries": [
    {"field": {"path": key, "title": key, "type": kind}, "isRequired": required}
    for key, kind, required in [("name", "String", True), ("email", "Email", True), ("resume", "File", True),
        ("location", "Location", True), ("background", "LongText", True), ("choice", "Enum", True)]
]}]}


def test_public_read_requires_exact_query_and_public_variables():
    class Request:
        method = "POST"
        url = "https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobPosting"
        post_data_json = {"operationName": "ApiJobPosting", "query": PUBLIC_QUERIES["ApiJobPosting"],
            "variables": {"organizationHostedJobsPageName": "0x", "jobPostingId": "fixture"}}
    request = Request()
    assert ashby_hosted.public_read(request, URL)
    request.post_data_json = {**request.post_data_json, "query": "mutation ApiJobPosting { apply }"}
    assert not ashby_hosted.public_read(request, URL)
    request.post_data_json = {**Request.post_data_json, "variables": {"organizationHostedJobsPageName": "0x", "jobPostingId": "fixture", "email": "candidate@example.invalid"}}
    assert not ashby_hosted.public_read(request, URL)


@pytest.mark.skipif(os.environ.get("TURIO_BROWSER_TESTS") != "1", reason="Opt-in isolated Chromium fixture.")
async def test_hosted_fill_reuses_original_file_and_leaves_custom_controls_and_submit_to_user():
    async with async_playwright() as driver:
        browser = await driver.chromium.launch(headless=True)
        page = await browser.new_page()
        requests = []
        async def deny(route):
            requests.append(route.request.url)
            await route.abort()
        await page.route("**/*", deny)
        await page.set_content(HTML)
        page._turio_hosted_form = copy.deepcopy(METADATA)
        schema = await ashby_hosted.schema(page)
        page._turio_hosted_form["id"] = "fresh-render-id"
        assert await ashby_hosted.schema(page) == schema
        assert len(schema["fields"]) == 6
        assert next(f for f in schema["fields"] if f["field_key"] == "location")["required"] is True
        snapshot = {"schema": schema, "resume_id": "owned", "answers": {
            "name": "Synthetic Candidate", "email": "candidate@example.invalid", "resume": "owned",
            "location": "London", "background": "My reviewed answer", "choice": "no"}}
        original = b"%PDF-1.4 synthetic-original"
        manual = await ashby_hosted.fill(page, snapshot, {"name": "original.pdf", "mimeType": "application/pdf", "buffer": original})
        assert manual == ["Location"]
        assert await page.locator("#name").input_value() == "Synthetic Candidate"
        assert await page.locator("#background").input_value() == "My reviewed answer"
        assert await page.locator('input[value="no"]').is_checked()
        assert await page.locator("#resume").evaluate("async el=>Array.from(new Uint8Array(await el.files[0].arrayBuffer()))") == list(original)
        assert not await page.evaluate("!!window.submitted") and requests == []
        changed = copy.deepcopy(snapshot)
        changed["schema"]["fields"][0]["label"] = "Changed name"
        with pytest.raises(AppError, match="changed"):
            await ashby_hosted.fill(page, changed, None)
        await page.locator("body").evaluate("el=>el.insertAdjacentHTML('beforeend','<div data-field-path=unexpected><label>Missing from metadata</label><input required></div>')")
        with pytest.raises(AppError, match="missing"):
            await ashby_hosted.schema(page)
        await browser.close()


@pytest.mark.skipif(os.environ.get("TURIO_BROWSER_TESTS") != "1", reason="Opt-in isolated Chromium fixture.")
async def test_default_radio_values_have_distinct_reviewed_choices():
    async with async_playwright() as driver:
        browser = await driver.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.set_content('<div data-field-path=source><label>How did you hear about this role</label>'
                '<label><input type=radio name=source>JobStash</label>'
                '<label><input type=radio name=source>Other</label></div>')
            page._turio_hosted_form = {"sections": [{"fieldEntries": [{"field": {
                "path": "source", "title": "How did you hear about this role", "type": "Enum"}, "isRequired": True}]}]}
            schema = await ashby_hosted.schema(page)
            assert schema["fields"][0]["options"] == [{"value": "JobStash", "label": "JobStash"}, {"value": "Other", "label": "Other"}]
            await ashby_hosted.fill(page, {"schema": schema, "resume_id": None, "answers": {"source": "Other"}}, None)
            assert not await page.get_by_label("JobStash", exact=True).is_checked()
            assert await page.get_by_label("Other", exact=True).is_checked()
        finally:
            await browser.close()


@pytest.mark.skipif(os.environ.get("TURIO_BROWSER_TESTS") != "1", reason="Opt-in isolated Chromium fixture.")
async def test_unanswered_optional_controls_are_left_untouched():
    async with async_playwright() as driver:
        browser = await driver.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.set_content('<div data-field-path=name><label>Name</label><input id=name></div>'
                '<div data-field-path=website><label>Website</label><input value="Employer default"></div>'
                '<div data-field-path=location><label>Location</label><input role=combobox></div>')
            page._turio_hosted_form = {"sections": [{"fieldEntries": [{"field": {"path": key, "title": key, "type": "String"},
                "isRequired": key == "name"} for key in ["name", "website", "location"]]}]}
            schema = await ashby_hosted.schema(page)
            manual = await ashby_hosted.fill(page, {"schema": schema, "resume_id": None, "answers": {"name": "Synthetic Candidate"}}, None)
            assert manual == []
            assert await page.locator('[data-field-path=website] input').input_value() == "Employer default"
        finally:
            await browser.close()


@pytest.mark.skipif(os.environ.get("TURIO_BROWSER_TESTS") != "1", reason="Opt-in isolated Chromium fixture.")
async def test_hosted_salary_instruction_is_preserved_in_schema():
    async with async_playwright() as driver:
        browser = await driver.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.set_content('<div data-field-path=salary><label>Expected salary</label><input placeholder="Numbers only"></div>')
            page._turio_hosted_form = {"sections": [{"fieldEntries": [{"field": {"path": "salary", "title": "Expected salary", "type": "String"},
                "descriptionHtml": "<p>Annual amount in USD</p>", "isRequired": True}]}]}
            schema = await ashby_hosted.schema(page)
            assert "Annual amount in USD" in (schema["fields"][0].get("help_text") or "")
            assert "Numbers only" in schema["fields"][0]["help_text"]
        finally:
            await browser.close()


@pytest.mark.skipif(os.environ.get("TURIO_BROWSER_TESTS") != "1", reason="Opt-in isolated visible Chromium fixture.")
async def test_visible_handoff_fills_then_waits_for_user_without_submitting(monkeypatch):
    from app.adapters import ashby_handoff
    from app.core.config import get_settings
    from playwright.async_api import Browser
    monkeypatch.setattr(get_settings(), "browser_automation_enabled", True)
    original_new_context = Browser.new_context
    browsers, mutations, results = [], [], []
    schema_value = None
    public_body = {"operationName": "ApiJobPosting", "query": PUBLIC_QUERIES["ApiJobPosting"],
        "variables": {"organizationHostedJobsPageName": "0x", "jobPostingId": "fixture"}}
    html = HTML + '<script>fetch("/api/non-user-graphql?op=ApiJobPosting",{method:"POST",headers:{"Content-Type":"application/json"},body:' + json.dumps(json.dumps(public_body)) + '})</script>'
    async def fixture(route):
        request = route.request
        if request.url == URL and request.method == "GET":
            await route.fulfill(content_type="text/html", body=html)
        elif ashby_hosted.public_read(request, URL):
            await route.fulfill(json={"data": {"jobPosting": {"applicationForm": METADATA}}})
        else:
            mutations.append(request.url)
            await route.abort()
    async def new_context(browser, **kwargs):
        browsers.append(browser)
        context = await original_new_context(browser, **kwargs)
        await context.route("**/*", fixture)
        return context
    monkeypatch.setattr(Browser, "new_context", new_context)
    async with async_playwright() as driver:
        browser = await driver.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(HTML)
        page._turio_hosted_form = copy.deepcopy(METADATA)
        schema_value = await ashby_hosted.schema(page)
        await browser.close()
    browsers.clear()
    checks = []
    async def confirm_fill():
        page = browsers[0].contexts[0].pages[0]
        assert await page.locator("#name").input_value() == ""
        return True
    monkeypatch.setattr(ashby_handoff, "confirm_fill", confirm_fill)
    async def inspect_and_close():
        page = browsers[0].contexts[0].pages[0]
        checks.append(await page.locator("#name").input_value())
        checks.append(await page.evaluate("!!window.submitted"))
        await browsers[0].close()
    def report(value, **kwargs):
        result = json.loads(value)
        results.append(result)
        if result.get("ready"):
            asyncio.create_task(inspect_and_close())
    monkeypatch.setattr(ashby_handoff, "print", report, raising=False)
    await ashby_handoff.main({"url": URL, "resume": None, "snapshot": {"schema": schema_value,
        "resume_id": None, "answers": {"name": "Reviewed Candidate", "email": "candidate@example.invalid", "background": "Reviewed", "choice": "yes"}}})
    assert results == [{"ready": True, "manual_fields": ["Location"]}]
    assert checks == ["Reviewed Candidate", False] and mutations == []
    assert not browsers[0].is_connected()


@pytest.mark.skipif(os.environ.get("TURIO_BROWSER_TESTS") != "1", reason="Opt-in isolated visible subprocess fixture.")
async def test_approved_handoff_uses_real_process_protocol_and_original_bytes(monkeypatch):
    from app.adapters import ashby
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), "browser_automation_enabled", True)
    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "true")
    async with async_playwright() as driver:
        browser = await driver.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(HTML)
        page._turio_hosted_form = copy.deepcopy(METADATA)
        schema_value = await ashby_hosted.schema(page)
        await browser.close()
    original_popen = ashby.subprocess.Popen
    processes = []
    # Fixture routing lives only in the child test wrapper; production IPC stays real.
    child = f"import sys; sys.path[:0] = {[str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parent)]!r}\n" + r'''
import asyncio, json
from playwright.async_api import Browser
from test_hosted_browser import HTML, METADATA, URL, PUBLIC_QUERIES
from app.adapters import ashby_hosted, ashby_handoff
contexts = []
new_context = Browser.new_context
body = {"operationName":"ApiJobPosting", "query":PUBLIC_QUERIES["ApiJobPosting"],
    "variables":{"organizationHostedJobsPageName":"0x","jobPostingId":"fixture"}}
html = HTML + '<script>fetch("/api/non-user-graphql?op=ApiJobPosting",{method:"POST",headers:{"Content-Type":"application/json"},body:' + json.dumps(json.dumps(body)) + '})</script>'
async def route_fixture(route):
    request = route.request
    if request.url == URL and request.method == "GET":
        await route.fulfill(content_type="text/html", body=html)
    elif ashby_hosted.public_read(request, URL):
        await route.fulfill(json={"data":{"jobPosting":{"applicationForm":METADATA}}})
    else:
        await route.abort()
async def context_fixture(browser, **kwargs):
    context = await new_context(browser, **kwargs)
    contexts.append(context)
    await context.route("**/*", route_fixture)
    return context
Browser.new_context = context_fixture
fill = ashby_hosted.fill
async def checked_fill(page, snapshot, resume):
    manual = await fill(page, snapshot, resume)
    assert await page.locator("#name").input_value() == "IPC Candidate"
    assert await page.locator("#background").input_value() == "IPC reviewed answer"
    assert await page.locator('input[value="no"]').is_checked()
    assert await page.locator("#resume").evaluate("async el=>Array.from(new Uint8Array(await el.files[0].arrayBuffer()))") == list(b"%PDF-1.4 IPC-original")
    assert not await page.evaluate("!!window.submitted")
    return manual
ashby_hosted.fill = checked_fill
report = print
def ready_report(value, **kwargs):
    report(value, **kwargs)
    if json.loads(value).get("ready"):
        asyncio.create_task(contexts[0].browser.close())
ashby_handoff.print = ready_report
asyncio.run(ashby_handoff.main(json.loads(sys.stdin.buffer.readline())))
'''
    def launch(args, **kwargs):
        if args == [sys.executable, "-m", "app.adapters.ashby_handoff"]:
            process = original_popen([sys.executable, "-c", child], **kwargs)
            processes.append(process)
            return process
        return original_popen(args, **kwargs)
    monkeypatch.setattr(ashby.subprocess, "Popen", launch)
    checks = []
    async def authorize(snapshot):
        checks.append(snapshot)
    async def resume(resume_id):
        assert resume_id == "owned"
        return "original.pdf", b"%PDF-1.4 IPC-original"
    adapter = ashby.AshbyAdapter(resume)
    adapter.authorize_handoff = authorize
    snapshot = {"schema": schema_value, "resume_id": "owned", "answers": {"name": "IPC Candidate",
        "email": "ipc@example.com", "resume": "owned", "location": "London", "background": "IPC reviewed answer", "choice": "no"}}
    try:
        result = await adapter.handoff(URL, snapshot)
        assert result == {"ready": True, "manual_fields": ["Location"]}
        assert len(checks) == 2
        assert await asyncio.to_thread(processes[0].wait, 10) == 0
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                await asyncio.to_thread(process.wait)
