"""Real-browser end-to-end check against the explicitly disposable UI server."""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend/tests"))
sys.path.insert(0, str(ROOT / "backend"))


async def main(url, output, application_fixture=False):
    from conftest import build_pdf
    from support import RESUME_TEXT
    from playwright.async_api import async_playwright

    checks, page_errors = [], []
    started = time.perf_counter()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=os.environ.get("BROWSER_EXECUTABLE_PATH"))
        context = await browser.new_context(viewport={"width": 1440, "height": 1000})
        sentinel = await context.request.get(url + "/api/health/fixture")
        assert sentinel.status == 200, "Refusing to run against a non-fixture server."
        fixture = await sentinel.json()
        assert fixture.get("fixture") == "turio-disposable-ui"
        assert fixture["application_fixture"] == application_fixture
        page = await context.new_page()
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        browser_version = browser.version
        await page.goto(url + "/signup")
        await page.get_by_label("Email address").fill(f"ui-{int(time.time())}@example.com")
        await page.get_by_label("Password", exact=True).fill("synthetic-test-password")
        await page.get_by_role("button", name="Create account").click()
        await page.wait_for_url("**/onboarding")
        await page.get_by_label("Choose PDF resume").set_input_files({"name": "fixture.pdf", "mimeType": "application/pdf", "buffer": build_pdf(RESUME_TEXT)})
        await page.get_by_role("button", name="Upload & extract").click()
        await page.get_by_text("Resume extracted. Check and correct the details below.", exact=True).wait_for()
        await page.get_by_label("Full name", exact=True).fill("UI Test Candidate")
        await page.get_by_label("Preferred roles", exact=False).fill("Python engineer")
        await page.get_by_role("button", name="Save profile", exact=True).click()
        await page.get_by_text("Profile saved.", exact=False).wait_for()
        checks.append("registration, PDF upload and profile edit")
        print("PASS: registration, PDF upload and profile edit", flush=True)
        cookies = await context.cookies()
        assert {c["name"] for c in cookies if c["name"].startswith("turio_")} == {"turio_access", "turio_refresh"}
        assert all(c["httpOnly"] and c["sameSite"] == "Lax" for c in cookies if c["name"].startswith("turio_"))
        assert await page.evaluate("localStorage.length + sessionStorage.length") == 0
        checks.append("HTTP-only session cookies; no browser-storage tokens")

        await page.goto(url + "/jobs")
        await page.get_by_role("button", name="Refresh inventory", exact=True).click()
        await page.get_by_text("Inventory refreshed: 0 new, 0 changed, 2 unchanged.", exact=True).wait_for()
        checks.append("durable inventory refresh through the worker")
        await page.get_by_label("Search", exact=True).fill("Python")
        await page.get_by_role("button", name="Search", exact=True).click()
        await page.get_by_role("heading", name="Python Engineer", exact=True).wait_for()
        await page.get_by_role("tab", name="For you").click()
        await page.get_by_role("button", name="Refresh my matches").click()
        await page.get_by_text("Recommendations updated", exact=False).wait_for()
        runs = await page.evaluate("async () => (await (await fetch('/api/runs?state=succeeded')).json()).data.runs")
        assert {run["kind"] for run in runs} == {"jobs_refresh", "matches_refresh"}
        checks.append("durable matching run reaches succeeded before recommendations render")
        await page.get_by_role("link", name="Python Engineer", exact=True).click()
        await page.wait_for_url("**/jobs/*")
        await page.get_by_role("button", name="Prepare application").click()
        await page.wait_for_url("**/applications/*")
        await page.get_by_role("button", name="Apply with Agent", exact=True).click()
        if application_fixture:
            await page.get_by_role("heading", name="Review your answers", exact=True).wait_for()
            name = page.get_by_label("Full name", exact=False)
            assert await name.is_disabled() and await name.input_value() == "UI Test Candidate"
            await page.get_by_text("Your stored original resume is selected.", exact=True).wait_for()
            await page.get_by_label("Are you legally authorized", exact=False).fill("No")
            async with page.expect_response(lambda r: r.url.endswith("/answers") and r.request.method == "POST"):
                await page.get_by_role("button", name="Save answers", exact=True).click()
            await page.get_by_role("button", name="Draft from profile", exact=True).click()
            await page.get_by_text("Factual starter from your profile", exact=False).wait_for()
            await page.get_by_role("button", name="Prepare final review", exact=True).click()
            await page.get_by_text("Complete required fields and confirm every draft before review.", exact=True).wait_for()
            narrative = page.locator(".field-row").filter(has=page.locator("textarea"))
            await narrative.get_by_label("I confirm this answer is accurate.", exact=True).check()
            async with page.expect_response(lambda r: r.url.endswith("/answers") and r.request.method == "POST"):
                await page.get_by_role("button", name="Save answers", exact=True).click()
            await page.get_by_role("button", name="Prepare final review", exact=True).click()
            submit = page.get_by_role("button", name="Approve & submit application", exact=True)
            await submit.wait_for()
            assert await submit.is_disabled()
            before = await (await context.request.get(url + "/api/health/fixture")).json()
            assert before["submissions"] == 0 and before["resume_writes"] == 1
            assert before["resume_reads"] >= 1
            await page.get_by_label("I have reviewed all answers and explicitly approve", exact=False).check()
            await submit.click()
            await page.get_by_text("Submission recorded via browser.", exact=False).wait_for()
            after = await (await context.request.get(url + "/api/health/fixture")).json()
            assert after["submissions"] == 1 and after["resume_writes"] == 1
            checks.append("stored resume/profile, missing answer, draft confirmation and explicit approval through real UI/API with a no-network adapter")
        else:
            await page.get_by_text("Browser assistance is disabled.", exact=False).wait_for()
        checks.append("job search, baseline recommendations, detail and application creation")
        if not application_fixture:
            checks.append("disabled live browser assistance fails visibly without submitting")
        print("PASS: jobs, recommendations, detail and safe application creation", flush=True)
        await page.get_by_role("combobox", name=re.compile(r"^Outcome")).select_option("interview")
        await page.get_by_label("Notes", exact=True).fill("Synthetic UI test only; no real employer contact.")
        await page.get_by_role("button", name="Save tracking").click()
        await page.get_by_text("Application updated.", exact=True).wait_for()
        if not application_fixture:
            await page.get_by_label("I submitted this application myself", exact=False).check()
            await page.get_by_role("button", name="Record manual submission").click()
            await page.get_by_text("Submission recorded via manual.", exact=False).wait_for()
        await page.goto(url + "/interviews")
        await page.get_by_text("Python Engineer", exact=True).wait_for()
        await page.goto(url + "/home")
        await page.get_by_role("heading", name="Keep going.", exact=False).wait_for()
        summary = await page.evaluate("async () => (await (await fetch('/api/applications/summary')).json()).data")
        assert summary["total"] == 1 and summary["interviews"] == 1 and summary["submitted"] == 1
        checks.append("application tracking, interview filter and real aggregate dashboard counts")
        print("PASS: tracking, interviews and dashboard aggregates", flush=True)
        output.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(output / "dashboard-desktop.png"), full_page=True)
        await page.set_viewport_size({"width": 390, "height": 844})
        for route in ["/home", "/jobs", "/profile", "/applications"]:
            await page.goto(url + route)
            await page.locator("main.workspace").wait_for()
            if route == "/home":
                await page.get_by_role("heading", name="Keep going.", exact=False).wait_for()
            elif route == "/profile":
                await page.get_by_label("Full name", exact=True).wait_for()
            else:
                await page.get_by_role("link", name="Python Engineer", exact=False).first.wait_for()
            assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), f"Overflow: {route}"
        checks.append("390px responsive layouts without document overflow")
        await page.screenshot(path=str(output / "applications-mobile.png"), full_page=True)
        response = await context.request.post(url + "/api/applications", headers={"Origin": "https://untrusted.invalid"}, data={"job_id": "invalid"})
        assert response.status == 403
        checks.append("cross-origin mutation rejected")
        await page.get_by_role("button", name="Sign out", exact=True).click()
        await page.wait_for_url(url + "/")
        assert not any(c["name"].startswith("turio_") for c in await context.cookies())
        checks.append("logout clears cookies")
        await page.evaluate("history.back()")
        await page.wait_for_url("**/login")
        checks.append("protected back-navigation after logout redirects to sign-in")
        assert not page_errors, page_errors
        await browser.close()
    result = {"scope": "Synthetic UI fixture, not PostgreSQL or real employer verification",
              "completed_at": datetime.now(timezone.utc).isoformat(),
              "duration_seconds": round(time.perf_counter() - started, 2),
              "browser": f"Chromium {browser_version}", "checks": checks, "page_errors": page_errors}
    (output / "ui-smoke.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:3001")
    parser.add_argument("--output", type=Path, default=ROOT / "data/ui-smoke")
    parser.add_argument("--application-fixture", action="store_true",
                        help="Exercise preparation and explicit approval only on the no-network fixture adapter.")
    args = parser.parse_args()
    asyncio.run(main(args.url, args.output, args.application_fixture))
