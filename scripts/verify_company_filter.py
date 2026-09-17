"""Local-stack company autocomplete regression; synthetic account, no applications."""
import asyncio
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]


async def main():
    checks, errors = [], []
    output = ROOT / "docs/evidence/company-filter-2026-09-16"
    output.mkdir(exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=os.environ.get("BROWSER_EXECUTABLE_PATH"))
        context = await browser.new_context(viewport={"width": 1440, "height": 1000})
        page = await context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        await page.goto("http://localhost:13000/signup")
        await page.get_by_label("Email address").fill(f"company-check-{int(time.time())}@example.com")
        await page.get_by_label("Password", exact=True).fill("synthetic-verification-password")
        await page.get_by_role("button", name="Create account").click()
        await page.wait_for_url("**/onboarding")
        await page.goto("http://localhost:13000/jobs")
        await page.locator(".job-card").first.wait_for()
        names = await page.locator(".company-name").all_text_contents()
        assert "Linear" not in names
        catalog = await page.evaluate("async () => (await (await fetch('/api/jobs/companies?limit=1')).json()).data")
        assert catalog["total"] == 3448
        platform_names = await page.evaluate("async () => (await (await fetch('/api/jobs/companies?q=ashby')).json()).data")
        # Ashby is itself a real catalog employer. Its name must not be confused
        # with matching every company's ATS metadata.
        assert 0 < platform_names["total"] < catalog["total"]
        assert all("ashby" in row["company"].casefold() or "ashby" in row["slug"].casefold()
                   for row in platform_names["companies"])
        checks.append("Full 3,448-company catalog is searchable independently of the current job page; search matches names/slugs, not ATS metadata")

        def jobs_response(response):
            return urlparse(response.url).path == "/api/jobs" and response.request.method == "GET"

        company = page.get_by_role("combobox", name="Company", exact=True)
        await company.fill("line")
        await page.get_by_role("option", name=re.compile(r"^Linear\s+linear$")).wait_for()
        await page.screenshot(path=str(output / "suggestions.png"))
        await company.press("ArrowDown")
        async with page.expect_response(jobs_response) as response:
            await company.press("Enter")
        selected = (await (await response.value).json())["data"]
        assert selected["total"] > 12 and all(job["company"] == "Linear" for job in selected["jobs"])
        assert await company.input_value() == "Linear"
        checks.append("Keyboard selection submits the canonical company name and returns its jobs")
        first_ids = {job["id"] for job in selected["jobs"]}
        async with page.expect_response(jobs_response) as response:
            await page.get_by_role("button", name="Next", exact=True).click()
        second = (await (await response.value).json())["data"]
        assert second["offset"] == 12 and second["total"] == selected["total"]
        assert not first_ids.intersection(job["id"] for job in second["jobs"])
        checks.append("Company-filtered pagination retains total and returns distinct pages")

        sample = next(job for job in selected["jobs"] if job["location"])
        await page.get_by_label("Search", exact=True).fill(sample["title"])
        await page.get_by_label("Location", exact=True).fill(sample["location"])
        await page.get_by_role("combobox", name="Platform", exact=True).select_option("ashby")
        async with page.expect_response(jobs_response) as response:
            await page.get_by_role("button", name="Search", exact=True).click()
        result = await response.value
        params = parse_qs(urlparse(result.url).query)
        assert params["company"] == ["Linear"] and params["ats"] == ["ashby"]
        assert params["q"] == [sample["title"]] and params["location"] == [sample["location"]]
        combined = (await result.json())["data"]
        assert combined["total"] >= 1 and combined["offset"] == 0
        assert all(job["company"] == "Linear" and job["ats"] == "ashby" and sample["location"].lower() in job["location"].lower()
                   and sample["title"].lower() in job["title"].lower() for job in combined["jobs"])
        checks.append("Search + Company + Location + Platform compose correctly and reset pagination")

        await page.get_by_label("Search", exact=True).fill("")
        await page.get_by_label("Location", exact=True).fill("")
        await company.fill("")
        await company.press("Escape")
        async with page.expect_response(jobs_response) as response:
            await page.get_by_role("button", name="Search", exact=True).click()
        platform = (await (await response.value).json())["data"]
        assert platform["total"] > selected["total"] and all(job["ats"] == "ashby" for job in platform["jobs"])
        checks.append("Clearing Company leaves Platform filtering independent")

        await company.fill("verce")
        option = page.get_by_role("option", name=re.compile(r"^Vercel\s+vercel$"))
        await option.wait_for()
        async with page.expect_response(jobs_response) as response:
            await option.click()
        empty = (await (await response.value).json())["data"]
        assert empty["total"] == 0 and not empty["jobs"]
        checks.append("Mouse selection discovers a real catalog company with no jobs and returns an honest empty result")
        await company.fill("not-a-real-company-xyz")
        await page.get_by_text("No catalog companies found.", exact=True).wait_for()
        assert await page.get_by_role("listbox", name="Company suggestions").get_by_role("option").count() == 0
        await company.fill("linear")
        await page.get_by_role("option", name=re.compile(r"^Linear\s+linear$")).wait_for()
        await company.press("Escape")
        assert await company.get_attribute("aria-expanded") == "false"
        checks.append("Unknown names are not fabricated; Escape dismisses the dropdown")
        await page.set_viewport_size({"width": 390, "height": 844})
        await company.press("ArrowDown")
        await page.get_by_role("option", name=re.compile(r"^Linear\s+linear$")).wait_for()
        assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        checks.append("Autocomplete preserves the mobile filter layout without horizontal overflow")
        await page.get_by_role("button", name="Sign out", exact=True).click()
        await page.wait_for_url("http://localhost:13000/")
        assert not errors, errors
        await browser.close()
    result = {"scope": "Real catalog/API/PostgreSQL, synthetic local verification account", "checks": checks, "page_errors": errors}
    (output / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
