"""Synthetic UI checks for missing-only prompts and bulk preparation. All APIs intercepted."""

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
        raise ValueError("Use a loopback frontend.")
    jobs = [{"id": f"job-{i}", "title": f"Engineer {i}", "company": f"Synthetic Company {i}",
        "location": "London", "description": "Synthetic role", "job_url": "https://employer.invalid/job",
        "application_url": "https://employer.invalid/job", "ats": "ashby", "required_skills": ["Python"]}
        for i in range(1, 4)]
    fields = [
        {"id": "linkedin", "field_key": "linkedin", "label": "Please share your LinkedIn profile URL",
         "input_type": "url", "required": True, "normalized_intent": "linkedin_url", "options": [],
         "value": "https://linkedin.com/in/synthetic", "value_source": "profile", "user_confirmed": True},
        {"id": "phone", "field_key": "phone", "label": "Phone", "input_type": "tel", "required": True,
         "normalized_intent": "phone", "options": [], "value": None, "value_source": "missing", "user_confirmed": False},
        {"id": "authorization", "field_key": "authorization", "label": "Work authorization answer",
         "input_type": "text", "required": True, "normalized_intent": "custom", "options": [],
         "value": "Previously confirmed synthetic answer", "value_source": "saved_answer", "user_confirmed": True},
    ]
    app = {"id": "fixture-app", "job": jobs[0], "application_url": "https://employer.invalid/job",
        "status": "needs_input", "outcome": None, "notes": None, "resume_id": "fixture-resume",
        "fields": copy.deepcopy(fields), "missing_fields": ["Phone"], "readiness_score": .67,
        "events": [], "review_token": None, "submitted_at": None, "submission_method": None}
    requests, unexpected, page_errors, checks, failures = [], [], [], [], []
    retry_failure = True
    allow_dialog = True
    hold_start = False
    release_start = asyncio.Event()
    bulk_apps = {}

    async def intercept(route):
        nonlocal retry_failure
        request = route.request
        parsed = urlparse(request.url)
        if parsed.netloc != origin.netloc:
            unexpected.append(request.url)
            await route.abort()
            return
        path = parsed.path
        if not path.startswith("/api/"):
            if request.method == "GET":
                await route.continue_()
            else:
                unexpected.append(path)
                await route.abort()
            return
        body = request.post_data_json if request.post_data else None
        requests.append({"path": path, "method": request.method, "body": body,
                         "key": request.headers.get("idempotency-key")})
        data, status, error = None, 200, None
        if path == "/api/auth/me":
            data = {"id": "fixture-user", "email": "fixture@example.invalid"}
        elif path == "/api/jobs":
            data = {"jobs": jobs, "total": 3, "limit": 12, "offset": 0}
        elif path == "/api/jobs/companies":
            data = []
        elif path == "/api/applications/fixture-app" and request.method == "GET":
            data = app
        elif path.endswith("/capability"):
            data = {"available": True, "reason": None}
        elif path == "/api/applications/fixture-app/answers":
            assert [item["field_id"] for item in body["answers"]] in [["phone"], ["phone", "authorization"]]
            assert all(item["save_for_reuse"] for item in body["answers"])
            for item in body["answers"]:
                field = next(f for f in app["fields"] if f["id"] == item["field_id"])
                field.update(value=item["value"], user_confirmed=item["user_confirmed"], value_source="user")
            app.update(missing_fields=[], readiness_score=1, status="ready_for_review")
            data = app
        elif path == "/api/applications/fixture-app/review":
            app.update(review_token="a" * 64, status="ready_for_review")
            data = app
        elif path == "/api/applications" and request.method == "POST":
            assert body["reuse_existing"] is True
            i = int(body["job_id"].split("-")[-1])
            if i == 2 and retry_failure:
                retry_failure = False
                status, error = 503, {"code": "FIXTURE_FAILURE", "message": "Synthetic preparation failure"}
            else:
                data = {**app, "id": f"bulk-{i}", "job": jobs[i - 1], "status": "created" if i < 3 else "ready_for_review",
                        "fields": [] if i < 3 else copy.deepcopy(app["fields"]), "review_token": None}
                bulk_apps.setdefault(i, copy.deepcopy(data))
        elif path.startswith("/api/applications/bulk-") and request.method == "GET" and not path.endswith("/capability"):
            i = int(path.split("bulk-")[-1])
            data = bulk_apps[i]
        elif path.startswith("/api/applications/bulk-") and path.endswith("/start"):
            if hold_start:
                await release_start.wait()
            i = int(path.split("bulk-")[-1].split("/")[0])
            assert body == {"ai_assist": False}
            data = {**app, "id": f"bulk-{i}", "job": jobs[i - 1], "status": "ready_for_review"}
            bulk_apps[i] = copy.deepcopy(data)
        else:
            unexpected.append(path)
            await route.abort()
            return
        await route.fulfill(status=status, json={"data": data, "error": error})

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=os.environ.get("BROWSER_EXECUTABLE_PATH"))
        context = await browser.new_context(viewport={"width": 1440, "height": 1000}, service_workers="block")
        await context.route("**/*", intercept)
        page = await context.new_page()
        page.set_default_timeout(10000)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("dialog", lambda d: asyncio.create_task(d.accept() if allow_dialog else d.dismiss()))
        output.mkdir(parents=True, exist_ok=True)
        try:
            await page.goto(url + "/applications/fixture-app")
            await page.get_by_label("Phone", exact=False).wait_for()
            assert await page.get_by_label("Please share your LinkedIn profile URL", exact=False).count() == 0, "Known LinkedIn must not be a prompt"
            assert await page.get_by_label("Work authorization answer", exact=False).count() == 0, "Saved confirmed answer must not be a prompt"
            await page.get_by_label("Phone", exact=False).fill("555-0100")
            await page.get_by_role("button", name="Save answers", exact=True).click()
            await page.get_by_text("Application updated.", exact=True).wait_for()
            assert await page.get_by_label("Phone", exact=False).count() == 0
            await page.get_by_text("View filled answers", exact=False).click()
            await page.get_by_text("555-0100", exact=True).wait_for()
            await page.get_by_role("button", name="Edit filled answers", exact=True).click()
            await page.get_by_label("Phone", exact=False).fill("555-0101")
            await page.get_by_role("button", name="Save answers", exact=True).click()
            await page.get_by_text("Application updated.", exact=True).wait_for()
            await page.get_by_role("button", name="Prepare final review", exact=True).click()
            submit = page.get_by_role("button", name="Approve & submit application", exact=True)
            await submit.wait_for()
            assert await submit.is_disabled()
            await page.set_viewport_size({"width": 390, "height": 844})
            assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
            await page.screenshot(path=str(output / "answers-mobile.png"), full_page=True)
            checks.append("known fields hidden, typed answers persist by default, summary edit, individual approval and mobile layout")
        except Exception as exc:
            failures.append(f"answers: {exc}")
        try:
            await page.set_viewport_size({"width": 1440, "height": 1000})
            await page.goto(url + "/jobs")
            await page.get_by_role("link", name="Engineer 1", exact=True).wait_for()
            assert await page.get_by_label("Select Engineer 1 at Synthetic Company 1", exact=True).count() == 1, "Job selection missing"
            for i in range(1, 4):
                await page.get_by_label(f"Select Engineer {i} at Synthetic Company {i}", exact=True).check()
            await page.get_by_role("button", name="Prepare selected applications", exact=True).click()
            await page.get_by_text("Synthetic preparation failure", exact=True).wait_for()
            retry = page.get_by_role("button", name="Retry failed applications", exact=True)
            await retry.wait_for()
            await retry.click()
            await page.get_by_text("Bulk preparation complete", exact=False).wait_for()
            creates = [r for r in requests if r["path"] == "/api/applications" and r["method"] == "POST"]
            assert [r["body"]["job_id"] for r in creates] == ["job-1", "job-2", "job-3", "job-2"]
            assert creates[1]["key"] == creates[3]["key"]
            assert len([r for r in requests if r["path"].endswith("/start")]) == 2, "Existing prepared application must not be restarted"
            assert not any(r["path"].endswith(("/approve-submit", "/handoff", "/review")) for r in requests if "bulk-" in r["path"])
            assert await page.get_by_role("link", name="Open application", exact=True).count() == 3
            await page.set_viewport_size({"width": 390, "height": 844})
            assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
            await page.screenshot(path=str(output / "bulk-mobile.png"), full_page=True)
            checks.append("bulk sequential preparation, partial failure, same-key retry, existing application reuse, result links and mobile layout")
            start_count = len([r for r in requests if r["path"].endswith("/start")])
            bulk_apps[1]["review_token"] = "c" * 64
            await page.get_by_role("button", name="Clear selection", exact=True).click()
            await page.get_by_role("button", name="Select visible jobs", exact=True).click()
            await page.get_by_role("button", name="Prepare selected applications", exact=True).click()
            await page.get_by_text("Bulk preparation complete", exact=False).wait_for()
            assert len([r for r in requests if r["path"].endswith("/start")]) == start_count, "Replayed create snapshots must not restart reviewed applications"
            assert bulk_apps[1]["review_token"] == "c" * 64
            checks.append("reselect reads current application state and preserves an existing review")
            await page.get_by_role("button", name="Clear selection", exact=True).click()
            bulk_apps.clear()
            await page.get_by_role("button", name="Select visible jobs", exact=True).click()
            count_before = len(requests)
            allow_dialog = False
            await page.get_by_role("button", name="Prepare selected applications", exact=True).click()
            assert len(requests) == count_before, "Declining bulk permission must not send any request"
            allow_dialog = True
            hold_start = True
            await page.get_by_role("button", name="Prepare selected applications", exact=True).click()
            await page.get_by_role("button", name="Stop after current job", exact=True).click()
            release_start.set()
            await page.get_by_text("Bulk preparation stopped.", exact=False).wait_for()
            created_after_stop = [r for r in requests[count_before:] if r["path"] == "/api/applications"]
            assert len(created_after_stop) == 1, "Stop must finish the current job only"
            hold_start = False
            await page.get_by_role("button", name="Prepare selected applications", exact=True).click()
            await page.get_by_text("Bulk preparation complete", exact=False).wait_for()
            assert [r["body"]["job_id"] for r in requests[count_before:] if r["path"] == "/api/applications"] == ["job-1", "job-2", "job-3"]
            checks.append("bulk permission decline, select visible, stop after current job and resume remaining selection")
        except Exception as exc:
            failures.append(f"bulk: {exc}")
        await browser.close()
    result = {"checks": checks, "failures": failures, "api_requests_intercepted": len(requests),
              "unexpected_requests": unexpected, "page_errors": page_errors}
    (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))
    assert not failures and not unexpected and not page_errors, result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:13000")
    parser.add_argument("--output", type=Path, default=Path(".verification/answer-reuse-ui"))
    args = parser.parse_args()
    asyncio.run(main(args.url.rstrip("/"), args.output))
