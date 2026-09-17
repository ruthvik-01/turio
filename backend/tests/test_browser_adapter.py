"""Opt-in native browser tests. All page requests terminate in in-memory fixtures."""

import asyncio
import os
import socket
from email import policy
from email.parser import BytesParser
from pathlib import Path
from urllib.parse import urlparse

import pytest

from app.adapters.ashby import AshbyAdapter
from app.core.config import get_settings
from app.core.errors import AppError

pytestmark = pytest.mark.skipif(
    os.environ.get("TURIO_BROWSER_TESTS") != "1",
    reason="Opt-in isolated Browser Use/Chromium fixture tests.",
)

FORM_URL = "https://jobs.ashbyhq.com/1password/turio-local-fixture"
ACTION_URL = "https://jobs.ashbyhq.com/1password/turio-fixture-submit"
ORIGINAL_PDF = b"%PDF-1.4\nsynthetic-original-resume-bytes\n%%EOF\n"


class FixtureSite:
    def __init__(self):
        self.mode = "normal"
        self.html = Path(__file__).with_name("fixtures").joinpath("native_application.html").read_text()
        self.posts = []
        self.unknown_requests = []
        self.pages = []
        self.runtimes = []
        self.reads = []
        self.navigation = False

    async def route(self, route):
        request = route.request
        if request.method == "GET" and request.url == FORM_URL:
            await route.fulfill(status=200, content_type="text/html", body=self.html.replace("__MODE__", self.mode))
        elif request.method == "POST":
            self.posts.append({"url": request.url, "body": request.post_data_buffer, "content_type": request.headers["content-type"]})
            if self.navigation:
                await route.fulfill(status=200, content_type="text/html", body="<h1>Application submitted</h1>")
            else:
                await route.fulfill(status=200, content_type="application/json", body='{"fixture":true}')
        else:
            self.unknown_requests.append((request.method, request.url))
            await route.abort()

    async def load_resume(self, resume_id):
        assert resume_id == "owned-resume"
        self.reads.append(resume_id)
        return "original.pdf", ORIGINAL_PDF

    async def authorize(self, snapshot):
        assert snapshot["resume_id"] == "owned-resume"

    def adapter(self, authorize=None):
        return AshbyAdapter(self.load_resume, authorize or self.authorize)

    @staticmethod
    def snapshot(schema):
        return {"schema": schema, "resume_id": "owned-resume", "profile_version": 1,
                "revision": 1, "url": FORM_URL, "answers": {
                    "name": "Synthetic Candidate", "email": "candidate@example.com",
                    "sponsorship": "no", "resume": "owned-resume",
                    "background": "Approved fixture answer.", "consent": True,
                }}


@pytest.fixture
async def site(monkeypatch):
    monkeypatch.setenv("ANONYMIZED_TELEMETRY", "false")
    from browser_use import Browser as Runtime
    import browser_use
    from playwright.async_api import Browser, async_playwright

    async with async_playwright() as driver:
        executable = driver.chromium.executable_path
    assert Path(executable).is_file(), "Install Chromium before opting into browser tests."
    settings = get_settings()
    monkeypatch.setattr(settings, "browser_automation_enabled", True)
    monkeypatch.setattr(settings, "browser_executable_path", executable)
    fixture = FixtureSite()
    original_new_context = Browser.new_context

    async def new_context(browser, **kwargs):
        context = await original_new_context(browser, **kwargs)
        # This terminal handler never continues a request to any employer.
        # The production guard is registered later and therefore runs first.
        await context.route("**/*", fixture.route)
        context.on("page", lambda page: fixture.pages.append(page))
        return context

    def runtime(*args, **kwargs):
        instance = Runtime(*args, **kwargs)
        fixture.runtimes.append(instance)
        return instance

    monkeypatch.setattr(Browser, "new_context", new_context)
    monkeypatch.setattr(browser_use, "Browser", runtime)
    try:
        yield fixture
    finally:
        # Only this fixture's owned runtimes, never the user's browser/profile.
        for instance in fixture.runtimes:
            if instance.cdp_url:
                try:
                    await asyncio.wait_for(instance.kill(), timeout=10)
                except Exception:
                    pass


def multipart(post):
    message = BytesParser(policy=policy.default).parsebytes(
        f"Content-Type: {post['content_type']}\r\nMIME-Version: 1.0\r\n\r\n".encode() + post["body"])
    return {part.get_param("name", header="content-disposition"):
            (part.get_filename(), part.get_payload(decode=True)) for part in message.iter_parts()}


async def test_native_inspection_labels_and_destination(site):
    schema = await site.adapter().inspect(FORM_URL)
    fields = {field["field_key"]: field for field in schema["fields"]}
    assert fields["sponsorship"]["label"] == "Sponsorship required"
    assert fields["resume"]["required"] is True
    assert schema["form_action"] == ACTION_URL
    assert schema["form_method"] == "post"
    assert not site.posts and not site.unknown_requests


async def test_review_fill_uploads_original_bytes_without_posting(site):
    adapter = site.adapter()
    schema = await adapter.inspect(FORM_URL)
    snapshot = site.snapshot(schema)
    await adapter.fill(FORM_URL, snapshot)
    assert site.reads == ["owned-resume"]
    assert site.posts == []


async def test_submit_uses_exact_reviewed_values_and_original_file(site):
    adapter = site.adapter()
    schema = await adapter.inspect(FORM_URL)
    result = await adapter.submit(FORM_URL, site.snapshot(schema))
    assert result["verified"] is True
    assert len(site.posts) == 1 and site.posts[0]["url"] == ACTION_URL
    fields = multipart(site.posts[0])
    assert fields["full_name"][1] == b"Synthetic Candidate"
    assert fields["email"][1] == b"candidate@example.com"
    assert fields["resume"] == ("original.pdf", ORIGINAL_PDF)
    assert fields["sponsorship"][1] == b"no"
    assert fields["phone"][1] == b""  # Unapproved defaults cannot be silently sent.
    assert "newsletter" not in fields


async def test_native_form_navigation_submission(site):
    site.navigation = True
    site.html = site.html.split("<script>")[0] + "</body></html>"
    adapter = site.adapter()
    result = await adapter.submit(FORM_URL, site.snapshot(await adapter.inspect(FORM_URL)))
    assert result["verified"]
    assert len(site.posts) == 1
    assert multipart(site.posts[0])["resume"] == ("original.pdf", ORIGINAL_PDF)


async def test_changed_form_action_stops_before_submission(site):
    adapter = site.adapter()
    snapshot = site.snapshot(await adapter.inspect(FORM_URL))
    site.html = site.html.replace(ACTION_URL, ACTION_URL + "-changed")
    with pytest.raises(AppError) as caught:
        await adapter.submit(FORM_URL, snapshot)
    assert caught.value.code == "CONFLICT"
    assert not site.posts


@pytest.mark.parametrize("mode", ["silent", "analytics", "tamper", "duplicate"])
async def test_confirmation_and_unrelated_or_modified_posts_do_not_prove_success(site, mode):
    adapter = site.adapter()
    snapshot = site.snapshot(await adapter.inspect(FORM_URL))
    site.mode = mode
    result = await adapter.submit(FORM_URL, snapshot)
    assert not result["verified"]
    assert len(site.posts) == (1 if mode == "duplicate" else 0)


async def test_changes_during_authorization_are_rejected(site):
    async def authorize(snapshot):
        await site.pages[-1].locator("#email").fill("changed-after-review@example.com")
    adapter = site.adapter(authorize)
    snapshot = site.snapshot(await adapter.inspect(FORM_URL))
    with pytest.raises(AppError):
        await adapter.submit(FORM_URL, snapshot)
    assert not site.posts


@pytest.mark.parametrize("markup", [
    '<div class="g-recaptcha">Manual challenge</div>',
    '<div role="combobox" aria-label="Unsupported choice">Pick</div>',
])
async def test_unsupported_controls_and_captcha_stop(site, markup):
    site.html = site.html.replace("</form>", markup + "</form>")
    with pytest.raises(AppError) as caught:
        await site.adapter().inspect(FORM_URL)
    assert caught.value.code == "UNSUPPORTED_APPLICATION"
    assert not site.posts


async def test_runtime_is_closed_after_context_exit(site):
    adapter = site.adapter()
    async with adapter.page(FORM_URL):
        endpoint = urlparse(site.runtimes[-1].cdp_url)
    with pytest.raises(OSError):
        connection = socket.create_connection((endpoint.hostname, endpoint.port), timeout=0.3)
        connection.close()


async def test_preapproval_writes_and_page_websockets_are_blocked(site):
    async with site.adapter().page(FORM_URL) as (page, _):
        result = await page.evaluate("""async action => {
            try { await fetch(action, {method:'POST',body:'not-approved'}); return 'sent'; }
            catch (_) { return 'blocked'; }
        }""", ACTION_URL)
        assert result == "blocked"
        websocket = await page.evaluate("""() => new Promise(resolve => {
            const ws = new WebSocket('wss://jobs.ashbyhq.com/fixture-socket');
            ws.onopen = () => { ws.close(); resolve('opened'); };
            ws.onclose = () => resolve('closed');
            ws.onerror = () => resolve('blocked');
            setTimeout(() => resolve('timeout'), 1000);
        })""")
        assert websocket in {"closed", "blocked"}
        assert page.context.service_workers == []
    assert site.posts == [] and site.unknown_requests == []


@pytest.mark.parametrize("failures", [2, 99])
async def test_fill_retries_are_bounded(site, monkeypatch, failures):
    from playwright.async_api import Locator

    adapter = site.adapter()
    snapshot = site.snapshot(await adapter.inspect(FORM_URL))
    original_fill = Locator.fill
    attempts = []

    async def flaky(locator, value, **kwargs):
        if await locator.get_attribute("id") == "name":
            attempts.append(value)
            if len(attempts) <= failures:
                raise RuntimeError("Synthetic transient fill failure.")
        return await original_fill(locator, value, **kwargs)

    monkeypatch.setattr(Locator, "fill", flaky)
    if failures == 2:
        await adapter.fill(FORM_URL, snapshot)
    else:
        with pytest.raises(AppError) as caught:
            await adapter.fill(FORM_URL, snapshot)
        assert caught.value.code == "BROWSER_ACTION_FAILED"
    assert len(attempts) == 3
    assert not site.posts


async def test_application_api_with_real_browser_and_original_resume(site, client, session, tmp_path, make_pdf, storage):
    from support import RESUME_TEXT, auth_headers, job_row, upload_resume, write_jobs_csv
    from app.services.job_ingestion import ingest_dataset

    headers = await auth_headers(client, "native-fixture@example.com")
    original = make_pdf(RESUME_TEXT)
    upload = await upload_resume(client, headers, original, filename="candidate-original.pdf")
    assert upload.status_code == 201
    resume_id = upload.json()["data"]["resume"]["id"]
    await client.patch("/api/v1/profiles/me", headers=headers, json={"sponsorship_required": False})
    path = write_jobs_csv(tmp_path / "native-fixture.csv", [job_row(url=FORM_URL, apply_url=FORM_URL)])
    await ingest_dataset(session, path=str(path))
    job = (await client.get("/api/v1/jobs", headers=headers)).json()["data"]["jobs"][0]
    created = await client.post("/api/v1/applications", headers={**headers, "Idempotency-Key": "native-create"},
                               json={"job_id": job["id"]})
    assert created.status_code == 201, created.text
    prefix = "/api/v1/applications/" + created.json()["data"]["id"]
    prepared = await client.post(prefix + "/start", headers=headers)
    assert prepared.status_code == 200, prepared.text
    fields = {field["field_key"]: field for field in prepared.json()["data"]["fields"]}
    assert fields["sponsorship"]["value"] == "no"
    assert fields["resume"]["value"] == resume_id
    assert fields["name"]["value"] == "Jane Doe"
    assert not site.posts
    answered = await client.post(prefix + "/answers", headers={**headers, "Idempotency-Key": "native-answer"},
                                json={"answers": [{"field_id": fields["consent"]["id"], "value": True}]})
    assert answered.status_code == 200, answered.text
    review = await client.post(prefix + "/review", headers=headers)
    assert review.status_code == 200, review.text
    assert not site.posts
    assert len(storage.get_calls) == 1
    request = {"approved": True, "review_token": review.json()["data"]["review_token"]}
    approval_headers = {**headers, "Idempotency-Key": "native-approval"}
    result = await client.post(prefix + "/approve-submit", headers=approval_headers, json=request)
    assert result.status_code == 200, result.text
    assert result.json()["data"]["status"] == "submitted", result.text
    assert result.json()["data"]["submission_method"] == "browser"
    assert len(site.posts) == 1
    assert multipart(site.posts[0])["resume"] == ("candidate-original.pdf", original)
    assert len(storage.get_calls) == 2 and storage.get_calls[0] == storage.get_calls[1]
    runtimes = len(site.runtimes)
    repeated = await client.post(prefix + "/approve-submit", headers=approval_headers, json=request)
    assert repeated.json()["data"] == result.json()["data"]
    assert len(site.posts) == 1 and len(site.runtimes) == runtimes
    event_types = [event["event_type"] for event in result.json()["data"]["events"]]
    assert event_types.index("review_ready") < event_types.index("submission_approved") < event_types.index("submitted")
