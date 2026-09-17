"""Local-stack browser regression; synthetic account, no employer submission.

Real API checks cover upload/storage/preparation and disabled-agent behavior.
The final-review UI contract is intercepted; native transport is tested separately.
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "backend/tests")]


async def main():
    from conftest import build_pdf
    from support import RESUME_TEXT
    from playwright.async_api import async_playwright

    output = ROOT / "docs/evidence/opportunity-ui-2026-09-16"
    output.mkdir(exist_ok=True)
    checks, errors = [], []
    base = "http://localhost:13000"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=os.environ.get("BROWSER_EXECUTABLE_PATH"))
        context = await browser.new_context(viewport={"width": 1440, "height": 1000})
        page = await context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        await page.goto(base + "/signup")
        await page.get_by_label("Email address").fill(f"opportunity-check-{int(time.time())}@example.com")
        await page.get_by_label("Password", exact=True).fill("synthetic-verification-password")
        await page.get_by_role("button", name="Create account").click()
        await page.wait_for_url("**/onboarding")
        await page.get_by_label("Choose PDF resume").set_input_files({
            "name": "synthetic-resume.pdf", "mimeType": "application/octet-stream", "buffer": build_pdf(RESUME_TEXT),
        })
        async with page.expect_response(lambda r: r.url.endswith("/api/resumes") and r.request.method == "POST") as uploaded:
            await page.get_by_role("button", name="Upload & extract").click()
        response = await uploaded.value
        assert response.status == 201, await response.text()
        resume = (await response.json())["data"]["resume"]
        await page.get_by_text("Resume extracted. Check and correct the details below.", exact=True).wait_for()
        checks.append("Generic-MIME PDF accepted through UI/proxy, processed and stored in the real stack")
        await page.goto(base + "/jobs")
        await page.get_by_label("Company", exact=True).fill("0x")
        async with page.expect_response(lambda r: "/api/jobs?" in r.url and "company=0x" in r.url) as jobs_response:
            await page.get_by_role("option").filter(has_text="0x").first.click()
        jobs = (await (await jobs_response.value).json())["data"]["jobs"]
        assert jobs and all(job["company"] == "0x" for job in jobs)
        await page.get_by_role("img", name="0x logo", exact=True).first.wait_for()
        await page.wait_for_function("() => [...document.querySelectorAll('img[alt=\"0x logo\"]')].some(img => img.naturalWidth > 0)")
        checks.append("Actual source-backed 0x logo loads in the existing company-icon slot")
        await page.get_by_role("link", name="View opportunity", exact=False).first.click()
        await page.get_by_role("heading", name="About this opportunity", exact=True).wait_for()
        description = await page.locator(".prose").inner_text()
        assert description.strip() and "**" not in description
        assert description == jobs[0]["description"]
        checks.append("About this opportunity renders the API's stored-description presentation without emphasis spam")
        await page.screenshot(path=str(output / "job-detail.png"), full_page=True)
        async with page.expect_response(lambda r: r.url.endswith("/api/applications") and r.request.method == "POST") as created:
            await page.get_by_role("button", name="Prepare application", exact=False).click()
        app = (await (await created.value).json())["data"]
        assert app["resume_id"] == resume["id"]
        await page.wait_for_url("**/applications/*")
        await page.get_by_text("Your stored resume and profile will be reused.", exact=False).wait_for()
        checks.append("Job → application preparation selects the already stored resume without another upload")
        await page.get_by_role("button", name="Apply with Agent", exact=True).click()
        await page.get_by_text("Browser assistance is disabled.", exact=False).wait_for()
        current = await page.evaluate("async id => (await (await fetch('/api/applications/' + id)).json()).data", app["id"])
        assert current["status"] == "created" and current["resume_id"] == resume["id"]
        checks.append("Apply with Agent reaches the existing start endpoint; disabled automation fails visibly without submission")
        await page.screenshot(path=str(output / "application-preparation.png"), full_page=True)

        # Intercept only this page's action responses to exercise the approval UI;
        # these are not real agent success or company-support claims.
        fields = [{"id": "fixture-resume", "field_key": "resume", "label": "Resume",
                   "input_type": "file", "required": True, "normalized_intent": "resume",
                   "options": [], "value": resume["id"], "value_source": "profile", "user_confirmed": True}]
        prepared = {**app, "fields": fields, "missing_fields": [], "status": "ready_for_review", "readiness_score": 1}
        submissions = []
        async def actions(route):
            action = route.request.url.rsplit("/", 1)[-1]
            if action == "start":
                data = {**prepared, "review_token": None}
            elif action == "review":
                data = {**prepared, "review_token": "intercepted-ui-review"}
            elif action == "approve-submit":
                body = route.request.post_data_json
                assert body == {"approved": True, "review_token": "intercepted-ui-review"}
                submissions.append(body)
                data = {**prepared, "status": "submitted", "submission_method": "browser", "review_token": None}
            else:
                await route.continue_()
                return
            await route.fulfill(json={"data": data, "error": None, "request_id": "ui-contract-fixture"})
        await page.route(f"**/api/applications/{app['id']}/*", actions)
        await page.get_by_role("button", name="Apply with Agent", exact=True).click()
        await page.get_by_text("Your stored original resume is selected.", exact=True).wait_for()
        await page.get_by_role("button", name="Prepare final review", exact=True).click()
        submit = page.get_by_role("button", name="Approve & submit application", exact=True)
        assert await submit.is_disabled() and not submissions
        await page.get_by_label("I have reviewed all answers and explicitly approve", exact=False).check()
        assert await submit.is_enabled()
        await submit.click()
        await page.get_by_text("Submission recorded via browser.", exact=False).wait_for()
        assert len(submissions) == 1
        checks.append("Intercepted UI contract: stored resume → final review → explicit checkbox → one approved action; no real submission")
        await page.unroute(f"**/api/applications/{app['id']}/*", actions)
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.goto(base + "/jobs")
        await page.locator(".job-card").first.wait_for()
        assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        checks.append("390px job layout remains within the viewport")
        await page.get_by_role("button", name="Sign out", exact=True).click()
        await page.wait_for_url(base + "/")
        assert not any(c["name"].startswith("turio_") for c in await context.cookies())
        checks.append("Logout clears session cookies")
        assert not errors, errors
        await browser.close()
    result = {"checks": checks, "page_errors": errors, "employer_submissions": 0,
              "scope": "Local PostgreSQL/MinIO stack; approval UI actions intercepted; synthetic verification account"}
    (output / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
