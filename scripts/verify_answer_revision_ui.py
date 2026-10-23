"""Rendered answer-save races using synthetic HTTP fixtures; no employer writes."""
import argparse
import asyncio
import copy
import json
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright


async def main(url, output):
    origin = urlparse(url)
    if origin.hostname not in {"localhost", "127.0.0.1"}:
        raise ValueError("Loopback frontend required")
    checks, unexpected, errors = [], [], []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        try:
            for mode in ["success", "safe-retry", "conflicting-edit"]:
                job = dict(id="fixture-job", company="Synthetic", title="Synthetic Engineer", ats="ashby",
                           job_url="https://employer.invalid/job", application_url="https://employer.invalid/job")
                app = dict(id="fixture-app", job=job, application_url=job["application_url"], status="needs_input",
                    outcome=None, notes=None, resume_id=None, revision=1, profile_version=1, review_token=None,
                    readiness_score=0, submission_method=None, submitted_at=None, created_at="2026-10-14T00:00:00Z",
                    missing_fields=["Fixture question"], events=[], fields=[dict(id="fixture-field", field_key="question",
                    label="Fixture question", input_type="text", required=True, normalized_intent="custom",
                    options=[], value=None, value_source="missing", user_confirmed=False)])
                saves = []
                async def intercept(route):
                    req = route.request
                    parsed = urlparse(req.url)
                    if parsed.netloc != origin.netloc:
                        unexpected.append(req.url)
                        await route.abort()
                        return
                    if not parsed.path.startswith("/api/"):
                        await route.continue_()
                        return
                    path = parsed.path
                    if path == "/api/auth/me":
                        data = dict(id="fixture-user", email="synthetic@example.invalid")
                    elif path.endswith("/capability"):
                        data = dict(available=True, reason=None)
                    elif path == "/api/applications/fixture-app/answers":
                        body = req.post_data_json
                        saves.append(body)
                        if len(saves) == 1 and mode != "success":
                            app["revision"] = 2
                            if mode == "conflicting-edit":
                                app["fields"][0].update(value="Concurrent answer", user_confirmed=True)
                            await route.fulfill(status=409, json=dict(data=None,
                                error=dict(code="STALE_REVISION", message="Fixture changed")))
                            return
                        assert body["expected_revision"] == app["revision"]
                        app["revision"] += 1
                        app["fields"][0].update(value=body["answers"][0]["value"], user_confirmed=True, value_source="user")
                        app["missing_fields"], app["status"] = [], "ready_for_review"
                        data = app
                    elif path == "/api/applications/fixture-app":
                        data = app
                    else:
                        unexpected.append(path)
                        data = None
                    await route.fulfill(json=dict(data=copy.deepcopy(data), error=None, request_id="fixture"))
                page = await browser.new_page()
                page.on("pageerror", lambda error: errors.append(str(error)))
                await page.route("**/*", intercept)
                await page.goto(url + "/applications/fixture-app")
                field = page.get_by_label("Fixture question", exact=False)
                await field.fill("User edit")
                await page.get_by_role("button", name="Save answers", exact=True).click()
                if mode == "conflicting-edit":
                    await page.get_by_text("These fields changed elsewhere.", exact=False).wait_for()
                    assert await field.input_value() == "User edit"
                    assert len(saves) == 1
                    assert app["fields"][0]["value"] == "Concurrent answer"
                else:
                    await page.get_by_text("Application updated.", exact=True).wait_for()
                    assert app["fields"][0]["value"] == "User edit"
                    assert len(saves) == (2 if mode == "safe-retry" else 1)
                checks.append(mode)
                await page.close()
        finally:
            await browser.close()
    result = dict(checks=checks, unexpected=unexpected, page_errors=errors)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))
    assert not unexpected and not errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:13100")
    parser.add_argument("--output", type=Path, default=Path(".runtime/persistence-revision-ui.json"))
    args = parser.parse_args()
    asyncio.run(main(args.url.rstrip("/"), args.output))
