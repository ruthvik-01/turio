"""Audit regressions against rendered UI; API requests use disposable fixtures."""
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
    job = dict(id="audit-job", title="Synthetic Engineer", company="Synthetic Company", ats="ashby",
        location="Test City", description="Fixture", job_url="https://employer.invalid/job",
        application_url="https://employer.invalid/job", required_skills=[])
    app = dict(id="audit-app", job=job, application_url=job["application_url"], status="ready_for_review",
        outcome=None, notes=None, resume_id="fixture-resume", revision=1, profile_version=1,
        review_token=None, readiness_score=1, submission_method=None, submitted_at=None,
        created_at="2026-10-14T00:00:00Z", updated_at="2026-10-14T00:00:00Z", missing_fields=[],
        manual_submission_required=False, events=[], fields=[dict(id="name", field_key="name",
        label="Full name", input_type="text", required=True, normalized_intent="full_name",
        options=[], value="Synthetic Candidate", value_source="profile", user_confirmed=True)])
    checks, requests, unexpected, page_errors = {}, [], [], []
    applications = [app]
    async def intercept(route):
        req = route.request
        parsed = urlparse(req.url)
        if parsed.netloc != origin.netloc:
            unexpected.append(req.url); await route.abort(); return
        if not parsed.path.startswith("/api/"):
            await route.continue_(); return
        path = parsed.path
        body = req.post_data_json if req.post_data else None
        requests.append(dict(path=path, method=req.method, body=body))
        data = None
        if path == "/api/auth/me": data = dict(id="fixture-user", email="synthetic@example.invalid")
        elif path == "/api/jobs": data = dict(jobs=[job], total=1, offset=0, limit=12)
        elif path == "/api/jobs/companies": data = []
        elif path == "/api/profiles/me": data = dict(version=1, full_name="Synthetic Candidate", skills=[])
        elif path == "/api/applications": data = dict(applications=applications, total=len(applications), offset=0, limit=12)
        elif path.endswith("/capability"): data = dict(available=True, reason=None)
        elif path.startswith("/api/applications/audit-app"):
            if path.endswith("/answers"):
                for item in body["answers"]:
                    field = next(f for f in app["fields"] if f["id"] == item["field_id"])
                    field.update(value=item["value"], user_confirmed=True,
                        value_source="user" if item["save_for_reuse"] else "application_only")
            elif req.method == "PATCH" and body.get("reset_to_review"):
                app["status"] = "ready_for_review"
            data = app
        else: unexpected.append(path)
        await route.fulfill(json=dict(data=copy.deepcopy(data), error=None, request_id="fixture"))
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        await page.route("**/*", intercept)
        await page.goto(url + "/login")
        checks["auth_submit_type"] = await page.locator("form button").get_attribute("type") == "submit"
        await page.goto(url + "/jobs")
        await page.get_by_role("heading", name="Bulk job applications").wait_for()
        checks["profile_navigation"] = await page.get_by_role("navigation", name="Main navigation").get_by_role("link", name="Profile", exact=True).count() == 1
        checks["platform_support_label"] = await page.get_by_label("Platform (Ashby supported)").count() == 1
        await page.goto(url + "/applications/audit-app")
        await page.get_by_text("View filled answers (1)").click()
        edit = page.get_by_role("button", name="Edit filled answers", exact=True)
        checks["profile_inline_edit"] = await edit.count() == 1
        if checks["profile_inline_edit"]:
            await edit.click()
            await page.get_by_label("Full name", exact=False).fill("Application Name")
            await page.get_by_role("button", name="Save answers", exact=True).click()
            await page.get_by_text("Application updated.", exact=True).wait_for()
            payload = next(r["body"] for r in reversed(requests) if r["path"].endswith("/answers"))
            checks["override_defaults_local"] = payload["answers"][0]["save_for_reuse"] is False
            if await page.locator("details.answer-summary").get_attribute("open") is None:
                await page.get_by_text("View filled answers (1)").click()
            await page.get_by_role("button", name="Edit filled answers", exact=True).click()
            await page.get_by_label("Full name", exact=False).fill("Reusable Name")
            await page.get_by_label("Save for future applications and update matching profile contact details.").check()
            await page.get_by_role("button", name="Save answers", exact=True).click()
            await page.get_by_text("Application updated.", exact=True).wait_for()
            payload = next(r["body"] for r in reversed(requests) if r["path"].endswith("/answers"))
            checks["override_reuse_opt_in"] = payload["answers"][0]["save_for_reuse"] is True
        app["status"] = "verification_failed"
        await page.reload()
        await page.get_by_text("The submission outcome is uncertain.", exact=False).wait_for()
        reset = page.get_by_role("button", name="Reset to review", exact=True)
        checks["uncertain_reset_action"] = await reset.count() == 1
        if checks["uncertain_reset_action"]:
            checks["reset_requires_ack"] = await reset.is_disabled()
            await page.get_by_label("I checked the employer site and confirmed this application was not submitted.").check()
            await reset.click()
            await page.get_by_text("Application updated.", exact=True).wait_for()
            checks["reset_sends_ack"] = any(r["body"] == dict(reset_to_review=True, confirmed_not_submitted=True) for r in requests if r["method"] == "PATCH")
        app["status"] = "needs_input"
        app["fields"].append(dict(id="custom", field_key="custom", label="Required shared answer", input_type="text",
            required=True, normalized_intent="custom", options=[], value=None, value_source="missing", user_confirmed=False))
        await page.goto(url + "/applications")
        await page.get_by_role("heading", name="Your next chapters.").wait_for()
        checks["tracker_bulk_controls"] = await page.get_by_role("heading", name="Bulk job applications").count() == 1
        if checks["tracker_bulk_controls"]:
            await page.get_by_role("checkbox", name="Select Synthetic Engineer at Synthetic Company").check()
            await page.get_by_role("heading", name="Answer once for selected applications").wait_for()
            await page.get_by_label("Required shared answer", exact=False).fill("Shared response")
            await page.get_by_role("button", name="Save shared answers", exact=True).click()
            await page.get_by_text("Shared answers saved across matching pending applications.", exact=False).wait_for()
            checks["tracker_shared_save"] = app["fields"][-1]["value"] == "Shared response"
            duplicate = copy.deepcopy(app)
            duplicate["id"] = "audit-app-2"
            applications.append(duplicate)
            await page.reload()
            choices = page.get_by_role("checkbox", name="Select Synthetic Engineer at Synthetic Company")
            await choices.first.wait_for()
            await choices.nth(0).check()
            await choices.nth(1).check()
            checks["tracker_same_job_drafts_independent"] = await page.get_by_text("2 selected", exact=True).count() == 1
            checks["tracker_preserves_application_ids"] = await page.locator('a[href="/applications/audit-app-2"]').count() > 0
            await page.get_by_role("button", name="Clear selection", exact=True).click()
            await choices.nth(0).check()
            request_start = len(requests)
            page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))
            await page.get_by_role("button", name="Prepare selected applications", exact=True).click()
            await page.get_by_text("Bulk preparation complete.", exact=False).wait_for()
            run_requests = requests[request_start:]
            checks["tracker_clear_preserves_selected_draft"] = not any(r["path"] == "/api/applications" and r["method"] == "POST" for r in run_requests)
            checks["tracker_reselect_reads_selected_id"] = any(r["path"] == "/api/applications/audit-app" and r["method"] == "GET" for r in run_requests)
        checks["no_external_requests"] = not unexpected
        checks["no_page_errors"] = not page_errors
        await page.screenshot(path=str(output.parent / "bug-audit-tracker.png"), full_page=True)
        await browser.close()
    output.write_text(json.dumps(dict(checks=checks, unexpected=unexpected, page_errors=page_errors), indent=2))
    print(json.dumps(checks))
    return all(checks.values())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:13000")
    parser.add_argument("--output", type=Path, default=Path("docs/evidence/bug-audit-fixes-2026-10-14.json"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    raise SystemExit(0 if asyncio.run(main(args.url.rstrip("/"), args.output)) else 1)
