"""Loopback UI regression using one synthetic account and a synthetic PDF.

Uses the existing stack. Never contacts an employer or submits an application.
Writes only local test-account/profile/application data and a bounded report.
"""
import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "backend/tests")]


async def main(url, output):
    from conftest import build_pdf
    from playwright.async_api import async_playwright

    origin = urlparse(url)
    if origin.hostname not in {"localhost", "127.0.0.1"} or origin.scheme != "http":
        raise ValueError("Use the existing loopback development stack only.")
    checks, errors, blocked = [], [], []
    output.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=os.environ.get("BROWSER_EXECUTABLE_PATH"))
        context = await browser.new_context(viewport={"width": 1440, "height": 1000})

        async def boundary(route):
            request = route.request
            if urlparse(request.url).netloc != origin.netloc or "/approve-submit" in request.url:
                if request.resource_type != "image":
                    blocked.append(urlparse(request.url).path)
                await route.abort()
            else:
                await route.continue_()

        await context.route("**/*", boundary)
        page = await context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        await page.goto(url + "/signup")
        await page.get_by_label("Email address").fill(f"usability-{uuid4().hex}@example.com")
        await page.get_by_label("Password", exact=True).fill("synthetic-verification-password")
        await page.get_by_role("button", name="Create account").click()
        await page.wait_for_url("**/onboarding")
        file_input = page.get_by_label("Choose PDF resume")
        upload = page.get_by_role("button", name="Upload resume", exact=True)
        assert await upload.is_disabled()
        await file_input.set_input_files({
            "name": "synthetic-projects.pdf", "mimeType": "application/pdf",
            "buffer": build_pdf("Synthetic Candidate\nSKILLS\nPython, FastAPI\nPROJECTS\n"
                                "Job Tracker\n- Built an API using Python.\n- Added FastAPI search.\n"),
        })
        async with page.expect_response(lambda r: urlparse(r.url).path == "/api/resumes") as response:
            await upload.click()
        uploaded = (await (await response.value).json())["data"]
        await page.get_by_text("Resume extracted. Check and correct the details below.", exact=True).wait_for()
        assert uploaded["resume"]["parser_version"] in {"rules-v2", "rules-v3-layout"}
        assert await page.get_by_label("Project name", exact=True).count() == 1
        assert await page.get_by_label("Project name", exact=True).input_value() == "Job Tracker"
        assert await page.get_by_label("Description", exact=False).input_value() == "Built an API using Python.\nAdded FastAPI search."
        assert await file_input.input_value() == "" and await upload.is_disabled()
        await page.reload()
        await page.get_by_label("Project name", exact=True).wait_for()
        assert await page.get_by_label("Project name", exact=True).input_value() == "Job Tracker"
        checks.append("Simple upload; project bullets grouped; parser v2; stored profile survives reload")
        await page.set_viewport_size({"width": 390, "height": 844})
        assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        await page.screenshot(path=str(output / "profile-mobile.png"), full_page=True)
        checks.append("390px profile layout has no horizontal overflow")
        await page.set_viewport_size({"width": 1440, "height": 1000})
        await page.goto(url + "/jobs")
        company = page.get_by_role("combobox", name="Company", exact=True)
        await company.click()
        await page.get_by_text("Type a name to search the full catalog.", exact=False).wait_for()
        await company.fill("supabase")
        await page.get_by_role("option", name=re.compile(r"^Supabase\s*supabase$")).wait_for()

        def jobs_response(response):
            return urlparse(response.url).path == "/api/jobs" and response.request.method == "GET"

        async with page.expect_response(jobs_response) as response:
            await company.press("Enter")
        selected = (await (await response.value).json())["data"]
        assert selected["total"] > 0 and all(job["company"] == "Supabase" for job in selected["jobs"])
        assert await company.input_value() == "Supabase"
        checks.append("Supabase autocomplete and Enter selection return actual Supabase jobs")
        if selected["total"] > 12:
            async with page.expect_response(jobs_response) as response:
                await page.get_by_role("button", name="Next", exact=True).click()
            next_page = (await (await response.value).json())["data"]
            assert next_page["total"] == selected["total"] and next_page["offset"] == 12
            assert not {j["id"] for j in selected["jobs"]} & {j["id"] for j in next_page["jobs"]}
            checks.append("Company pagination preserves totals and distinct pages")
        job = selected["jobs"][0]
        await page.get_by_label("Search", exact=True).fill(job["title"])
        await page.get_by_label("Location", exact=True).fill(job["location"] or "")
        await page.get_by_label("Platform", exact=False).select_option("ashby")
        async with page.expect_response(jobs_response) as response:
            await page.get_by_role("button", name="Search", exact=True).click()
        combined = (await (await response.value).json())["data"]
        assert combined["offset"] == 0 and any(row["id"] == job["id"] for row in combined["jobs"])
        assert all(row["company"] == "Supabase" and row["ats"] == "ashby" for row in combined["jobs"])
        checks.append("Search/company/location/platform combine and reset pagination")
        await page.goto(url + "/jobs/" + job["id"])
        await page.get_by_role("button", name="Prepare application", exact=False).click()
        await page.wait_for_url("**/applications/*")
        await page.wait_for_selector("p[role='status']")
        status_text = await page.locator("p[role='status']").inner_text()
        if "Browser assistant ready" in status_text:
            checks.append("Browser assistant ready for Ashby trial company; permission prompt enforced")
        else:
            assert "Browser assistance is disabled" in status_text or "Continue manually" in status_text
            assert await page.get_by_role("button", name="Apply with Agent", exact=True).is_disabled()
            checks.append("Stored resume reused; disabled automation explained before clicking; no submission")
        await page.get_by_text("Your stored resume and profile will be reused.", exact=False).wait_for()
        app_id = urlparse(page.url).path.split("/")[-1]
        stored_app = await page.evaluate("async id => (await (await fetch('/api/applications/' + id)).json()).data", app_id)
        assert stored_app["resume_id"] == uploaded["resume"]["id"]
        assert stored_app["status"] == "created" and stored_app["submitted_at"] is None
        assert not errors and not blocked
        report = {"checks": checks, "supabase_jobs": selected["total"], "page_errors": errors,
                  "unexpected_requests": blocked, "scope": "Synthetic account/PDF; existing local stack; external images blocked; no employer requests"}
        (output / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report))
        await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:13000")
    parser.add_argument("--output", type=Path, default=Path(".runtime/profile-company-ui"))
    args = parser.parse_args()
    asyncio.run(main(args.url.rstrip("/"), args.output))
