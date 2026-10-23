"""Frontend-only synthetic contract checks; every API call is intercepted.

Not a backend integration test or employer-flow validation. Never forwards API
requests, uploads a real resume, or contacts an employer.
"""
import argparse
import asyncio
import copy
import json
import os
from pathlib import Path
from urllib.parse import urlparse


async def main(url, output):
    from playwright.async_api import async_playwright

    origin = urlparse(url)
    if origin.hostname not in {"localhost", "127.0.0.1"} or origin.scheme != "http":
        raise ValueError("Use an existing loopback frontend only.")
    app_id = "11111111-1111-4111-8111-111111111111"
    resume_id = "22222222-2222-4222-8222-222222222222"
    prefix = f"/api/applications/{app_id}"
    fields = [
        {"id": "name", "field_key": "name", "label": "Full name", "input_type": "text",
         "required": True, "normalized_intent": "full_name", "options": [],
         "value": "Synthetic UI Candidate", "value_source": "profile", "user_confirmed": True},
        {"id": "resume", "field_key": "resume", "label": "Resume", "input_type": "file",
         "required": True, "normalized_intent": "resume", "options": [],
         "value": resume_id, "value_source": "profile", "user_confirmed": True},
        {"id": "phone", "field_key": "phone", "label": "Phone", "input_type": "tel",
         "required": True, "normalized_intent": "phone", "options": [],
         "value": None, "value_source": "missing", "user_confirmed": False},
        {"id": "background", "field_key": "background", "label": "Describe your relevant experience",
         "input_type": "textarea", "required": True, "normalized_intent": "custom", "options": [],
         "value": None, "value_source": "missing", "user_confirmed": False},
    ]
    app = {"id": app_id, "job": {"id": "fixture-job", "title": "Synthetic UI Engineer",
           "company": "Synthetic UI Fixture", "company_logo_url": None},
           "application_url": "https://employer.invalid/never-opened", "status": "created",
           "outcome": None, "notes": None, "resume_id": resume_id, "fields": [],
           "missing_fields": [], "readiness_score": 0, "events": [], "review_token": None,
           "submitted_at": None, "submission_method": None}
    requests, approvals, handoffs, unexpected, errors = [], [], [], [], []

    async def intercept(route):
        request = route.request
        parsed = urlparse(request.url)
        if parsed.netloc != origin.netloc:
            unexpected.append(request.url)
            await route.abort()
            return
        if not parsed.path.startswith("/api/"):
            if request.method in {"GET", "HEAD"}:
                await route.continue_()
            else:
                unexpected.append(request.url)
                await route.abort()
            return
        path = parsed.path
        if path == prefix + "/capability" and request.method == "GET":
            requests.append((request.method, path))
            await route.fulfill(content_type="application/json",
                                body=json.dumps({"data": {"available": True, "reason": None}, "error": None}))
            return
        requests.append((request.method, path))
        data, error, status = None, None, 200
        if path == "/api/auth/me" and request.method == "GET":
            data = {"id": "fixture-user", "email": "fixture@example.invalid"}
        elif path == prefix and request.method == "GET":
            data = app
        elif path == prefix + "/start" and request.method == "POST":
            app.update(fields=copy.deepcopy(fields), status="needs_input", review_token=None)
            data = app
        elif path == prefix + "/answers" and request.method == "POST":
            for item in request.post_data_json["answers"]:
                assert item["field_id"] not in {"name", "resume"}, "Profile values must not be resubmitted."
                field = next(f for f in app["fields"] if f["id"] == item["field_id"])
                field.update(value=item["value"], user_confirmed=item["user_confirmed"], value_source="user")
            app["review_token"] = None
            data = app
        elif path == prefix + "/fields/background/draft" and request.method == "POST":
            app["fields"][-1].update(value="Synthetic profile facts only.", value_source="draft", user_confirmed=False)
            data = app
        elif path == prefix + "/review" and request.method == "POST":
            if any((f["required"] and not f["value"]) or (f["value"] and not f["user_confirmed"]) for f in app["fields"]):
                status, error = 422, {"message": "Complete required fields and confirm every draft before review."}
            else:
                app.update(review_token="a" * 64, status="ready_for_review", readiness_score=1)
                data = app
        elif path == prefix + "/approve-submit" and request.method == "POST":
            assert not app.get("manual_submission_required"), "Hosted form must not use automatic submission."
            assert request.post_data_json == {"approved": True, "review_token": app["review_token"]}
            approvals.append(request.headers.get("idempotency-key"))
            if len(approvals) == 1:
                status, error = 503, {"message": "Synthetic retryable response failure."}
            else:
                app.update(status="submitted", submission_method="browser", review_token=None)
                data = app
        elif path == prefix + "/handoff" and request.method == "POST":
            assert request.post_data_json == {"approved": True, "review_token": app["review_token"]}
            handoffs.append(request.headers.get("idempotency-key"))
            app.update(review_token=None, events=[{"event_type": "manual_handoff_ready", "created_at": "2026-10-12T06:00:00Z", "event_data": {"message": "The employer browser is open. Submit yourself."}}])
            data = app
        else:
            unexpected.append(request.url)
            await route.abort()
            return
        await route.fulfill(status=status, json={"data": data, "error": error, "request_id": "synthetic-ui-contract"})

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=os.environ.get("BROWSER_EXECUTABLE_PATH"))
        context = await browser.new_context(viewport={"width": 1440, "height": 1000}, service_workers="block")
        await context.route("**/*", intercept)
        page = await context.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("dialog", lambda d: asyncio.create_task(d.accept()))
        await page.goto(url + f"/applications/{app_id}")
        await page.get_by_role("button", name="Apply with Agent", exact=True).click()
        await page.get_by_label("Phone", exact=False).wait_for()
        assert await page.get_by_label("Full name", exact=False).count() == 0
        await page.get_by_text("View filled answers", exact=False).click()
        await page.get_by_text("Synthetic UI Candidate", exact=True).wait_for()
        await page.get_by_text("Your stored original resume is selected.", exact=True).wait_for()
        await page.get_by_role("button", name="Prepare final review", exact=True).click()
        await page.get_by_text("Complete required fields and confirm every draft before review.", exact=True).wait_for()
        await page.get_by_label("Phone", exact=False).fill("555-0100")
        async with page.expect_response(lambda r: r.url.endswith("/answers")):
            await page.get_by_role("button", name="Save answers", exact=True).click()
        await page.get_by_role("button", name="Draft from profile", exact=True).click()
        await page.get_by_text("Factual starter from your profile", exact=False).wait_for()
        await page.get_by_role("button", name="Prepare final review", exact=True).click()
        await page.get_by_text("Complete required fields and confirm every draft before review.", exact=True).wait_for()
        narrative = page.locator(".field-row").filter(has=page.locator("textarea"))
        await narrative.get_by_label("I confirm this answer is accurate.", exact=True).check()
        async with page.expect_response(lambda r: r.url.endswith("/answers")):
            await page.get_by_role("button", name="Save answers", exact=True).click()
        await page.get_by_role("button", name="Prepare final review", exact=True).click()
        submit = page.get_by_role("button", name="Approve & submit application", exact=True)
        await submit.wait_for()
        assert await submit.is_disabled() and not approvals
        await page.get_by_label("I have reviewed all answers and explicitly approve", exact=False).check()
        await page.get_by_role("button", name="Edit saved answers", exact=True).click()
        await page.get_by_label("Phone", exact=False).fill("555-0101")
        assert await submit.count() == 0
        assert await page.get_by_role("button", name="Prepare final review", exact=True).is_disabled()
        async with page.expect_response(lambda r: r.url.endswith("/answers")):
            await page.get_by_role("button", name="Save answers", exact=True).click()
        await page.get_by_role("button", name="Prepare final review", exact=True).click()
        await submit.wait_for()
        assert await submit.is_disabled()
        await page.set_viewport_size({"width": 390, "height": 844})
        assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        await page.get_by_label("I have reviewed all answers and explicitly approve", exact=False).check()
        await submit.click()
        await page.get_by_text("Synthetic retryable response failure.", exact=True).wait_for()
        await submit.click()
        await page.get_by_text("Submission recorded via browser.", exact=False).wait_for()
        assert len(approvals) == 2 and approvals[0] and approvals[0] == approvals[1]
        assert not unexpected and not errors, (unexpected, errors)
        output.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(output / "application-mobile.png"), full_page=True)
        app.update(status="ready_for_review", submission_method=None, manual_submission_required=True, review_token="b" * 64)
        await page.reload()
        handoff = page.get_by_role("button", name="Open filled employer form", exact=True)
        await handoff.wait_for()
        assert await handoff.is_disabled()
        assert await page.get_by_role("button", name="Approve & submit application", exact=True).count() == 0
        await page.get_by_label("I approve sending these reviewed answers and my original resume to the employer form. I will submit it myself.", exact=True).check()
        await handoff.click()
        await page.locator(".notice.success").get_by_text("The employer browser is open. Submit yourself.", exact=True).wait_for()
        assert len(handoffs) == 1 and len(approvals) == 2
        assert not unexpected and not errors, (unexpected, errors)
        await page.screenshot(path=str(output / "manual-handoff-mobile.png"), full_page=True)
        result = {"scope": "Frontend only; all API responses intercepted, no backend writes or employer requests",
                  "checks": ["stored profile/resume UI", "missing field rejection", "draft confirmation required",
                             "explicit approval required", "edits require saving and fresh approval",
                             "390px layout", "same-key retry after simulated failure", "hosted explicit fill approval and manual submission"],
                  "api_requests_intercepted": len(requests), "unexpected_requests": unexpected, "page_errors": errors}
        (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result))
        await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:13000")
    parser.add_argument("--output", type=Path, default=Path(".runtime/application-ui-contract"))
    args = parser.parse_args()
    asyncio.run(main(args.url.rstrip("/"), args.output))
