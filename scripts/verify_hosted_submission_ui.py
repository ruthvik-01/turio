"""Intercepted UI contracts: multi-choice answers, explicit approval, closed jobs."""
import argparse
import asyncio
import copy
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright


async def main(url, output):
    origin = urlparse(url)
    if origin.scheme != "http" or origin.hostname not in {"127.0.0.1", "localhost"}:
        raise ValueError("Loopback fixture frontend required")
    jobs = [{"id": f"job-{kind}", "title": f"{kind.title()} Engineer", "company": "Synthetic Company", "location": "Test City",
             "description": "Synthetic job", "job_url": "https://employer.invalid/job", "application_url": "https://employer.invalid/job",
             "ats": "ashby", "required_skills": []} for kind in ("closed", "open")]

    def app(job, identifier):
        return {"id": identifier, "job": job, "application_url": job["application_url"], "status": "needs_input",
                "resume_id": "synthetic-resume", "profile_version": 1, "manual_submission_required": False,
                "notes": None, "outcome": None, "events": [], "review_token": None, "submitted_at": None,
                "submission_method": None, "readiness_score": 0, "missing_fields": ["Segments", "Relatives"],
                "fields": [{"id": "segments", "field_key": "segments", "label": "Segments", "input_type": "multiselect",
                            "required": True, "options": [{"value": "SMB", "label": "SMB"}, {"value": "Enterprise", "label": "Enterprise"}],
                            "value": None, "value_source": "missing", "user_confirmed": False},
                           {"id": "relatives", "field_key": "relatives", "label": "Relatives", "input_type": "select",
                            "required": True, "options": [{"value": "true", "label": "Yes"}, {"value": "false", "label": "No"}],
                            "value": None, "value_source": "missing", "user_confirmed": False}]}

    current = app(jobs[1], "hosted-fixture")
    bulk_apps, requests, unexpected, errors, checks = {}, [], [], [], []
    closed = False

    async def intercept(route):
        nonlocal closed
        request = route.request
        parsed = urlparse(request.url)
        if parsed.netloc != origin.netloc:
            unexpected.append("external request"); await route.abort(); return
        if not parsed.path.startswith("/api/"):
            if request.method in {"GET", "HEAD"}: await route.continue_()
            else: unexpected.append(parsed.path); await route.abort()
            return
        body = request.post_data_json if request.post_data else None
        path = parsed.path
        requests.append({"path": path, "method": request.method, "body": body})
        data, status, error = None, 200, None
        if path == "/api/auth/me": data = {"id": "fixture-user", "email": "synthetic@example.invalid"}
        elif path == "/api/jobs": data = {"jobs": [j for j in jobs if not closed or j["id"] != "job-closed"], "total": 1 if closed else 2, "limit": 12, "offset": 0}
        elif path == "/api/jobs/companies": data = []
        elif path == "/api/applications" and request.method == "POST":
            job = next(j for j in jobs if j["id"] == body["job_id"])
            bulk_apps[job["id"]] = app(job, job["id"])
            bulk_apps[job["id"]]["status"] = "created"
            data = bulk_apps[job["id"]]
        elif path.startswith("/api/applications/"):
            parts = path.split("/")
            identifier, action = parts[3], parts[4] if len(parts) > 4 else ""
            value = current if identifier == current["id"] else bulk_apps[identifier]
            if not action: data = value
            elif action == "capability": data = {"available": True, "reason": None}
            elif action == "answers":
                assert {a["field_id"]: a["value"] for a in body["answers"]} == {"segments": ["SMB", "Enterprise"], "relatives": "false"}
                for answer in body["answers"]:
                    field = next(f for f in value["fields"] if f["id"] == answer["field_id"])
                    field.update(value=answer["value"], user_confirmed=True, value_source="user")
                value.update(status="ready_for_review", missing_fields=[]); data = value
            elif action == "review": value["review_token"] = "a" * 64; data = value
            elif action == "approve-submit":
                assert body == {"approved": True, "review_token": "a" * 64}
                value.update(status="submitted", submission_method="browser"); data = value
            elif action == "start" and identifier == "job-closed":
                closed = True; status = 404; error = {"code": "JOB_UNAVAILABLE", "message": "Posting removed; hidden from active jobs."}
            elif action == "start": value["status"] = "needs_input"; data = value
            else: unexpected.append(path); await route.abort(); return
        else: unexpected.append(path); await route.abort(); return
        await route.fulfill(status=status, json={"data": copy.deepcopy(data), "error": error, "request_id": "fixture"})

    async with async_playwright() as driver:
        browser = await driver.chromium.launch(headless=True)
        try:
            page = await browser.new_page(viewport={"width": 1366, "height": 900})
            page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))
            page.on("pageerror", lambda e: errors.append(str(e)))
            await page.route("**/*", intercept)
            await page.goto(url + "/applications/hosted-fixture")
            await page.get_by_label("Segments", exact=False).select_option(["SMB", "Enterprise"])
            await page.get_by_label("Relatives", exact=False).select_option("false")
            await page.get_by_role("button", name="Save answers", exact=True).click()
            await page.get_by_text("Your answers are ready", exact=True).wait_for()
            await page.locator("summary").filter(has_text="View filled answers").click()
            await page.get_by_text("SMB, Enterprise", exact=True).wait_for()
            await page.get_by_text("No", exact=True).wait_for()
            assert not any(r["path"].endswith("approve-submit") for r in requests)
            checks.append("multiple selections and No save/display correctly; no early submission")
            await page.get_by_role("button", name="Prepare final review", exact=True).click()
            approval = page.get_by_role("button", name="Approve & submit application", exact=True)
            await approval.wait_for()
            assert await approval.is_disabled()
            await page.get_by_label("I have reviewed all answers and explicitly approve submitting this application.", exact=True).check()
            await approval.click()
            await page.get_by_text("submitted", exact=False).first.wait_for()
            assert len([r for r in requests if r["path"].endswith("approve-submit")]) == 1
            checks.append("supported hosted form submits once after explicit approval")

            await page.goto(url + "/jobs")
            await page.get_by_label("Select Closed Engineer at Synthetic Company", exact=True).check()
            await page.get_by_label("Select Open Engineer at Synthetic Company", exact=True).check()
            await page.get_by_role("button", name="Prepare selected applications", exact=True).click()
            await page.get_by_label("Select Closed Engineer at Synthetic Company", exact=True).wait_for(state="detached")
            await page.get_by_label("Select Open Engineer at Synthetic Company", exact=True).wait_for()
            await page.get_by_text("1 selected", exact=True).wait_for()
            checks.append("confirmed removed posting disappears and is deselected; open posting remains")
            assert not unexpected and not errors, {"unexpected": unexpected, "errors": errors}
        finally:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps({"checks": checks, "requests": requests, "closed": closed,
                                          "unexpected": unexpected, "page_errors": errors}, indent=2), encoding="utf-8")
            if errors or len(checks) < 3:
                print("UI_DIAGNOSTIC", json.dumps({"checks": checks, "closed": closed, "errors": errors,
                    "requests": [{"path": r["path"], "method": r["method"]} for r in requests[-12:]],
                    "text": (await page.locator("body").inner_text())[-2400:]}), flush=True)
            await page.screenshot(path=str(output.with_suffix(".png")), full_page=True)
            await browser.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"checks": checks, "requests": len(requests), "unexpected": unexpected, "page_errors": errors}, indent=2), encoding="utf-8")
    print(json.dumps({"checks": checks, "unexpected": unexpected, "page_errors": errors}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:13002")
    parser.add_argument("--output", type=Path, default=Path(".runtime/hosted-auto/ui.json"))
    args = parser.parse_args()
    asyncio.run(main(args.url.rstrip("/"), args.output))
