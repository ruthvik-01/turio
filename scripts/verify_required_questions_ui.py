"""Required-only prompts and salary guidance; every API call is intercepted."""
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
    assert origin.hostname in {"127.0.0.1", "localhost"} and origin.scheme == "http"
    def field(key, label, required, value=None, source="missing", confirmed=False, **extra):
        return {"id": key, "field_key": key, "label": label, "required": required, "value": value,
            "value_source": source, "user_confirmed": confirmed, "input_type": "text", "normalized_intent": "custom", "options": [], **extra}
    app = {"id": "required-only", "job": {"id": "job", "company": "Synthetic employer", "title": "Engineer"},
        "status": "needs_input", "application_url": "https://employer.invalid/job", "resume_id": "resume",
        "fields": [field("salary", "Expectation Salary per annum", True, help_text="Currency: not specified by employer. Pay period: annual. Include currency, e.g. USD 120000/year or INR 1200000/year."),
                   field("cover", "Optional cover letter", False, input_type="textarea"),
                   field("ai", "Optional AI suggestion", False, "Unconfirmed suggestion", "ai_profile"),
                   field("name", "Name", True, "Synthetic Candidate", "profile", True)],
        "missing_fields": ["Expectation Salary per annum"], "readiness_score": .5, "review_token": None,
        "notes": None, "outcome": None, "events": [], "submission_method": None, "submitted_at": None}
    requests, unexpected, errors = [], [], []
    async def intercept(route):
        request = route.request
        parsed = urlparse(request.url)
        if parsed.netloc != origin.netloc:
            unexpected.append(request.url); await route.abort(); return
        if not parsed.path.startswith("/api/"):
            await route.continue_(); return
        path = parsed.path
        requests.append(path)
        if path == "/api/auth/me": data = {"id": "user", "email": "synthetic@example.invalid"}
        elif path.endswith("/capability"): data = {"available": True, "reason": None}
        elif path == "/api/applications/required-only": data = app
        elif path.endswith("/answers"):
            answers = request.post_data_json["answers"]
            assert len(answers) == 1 and answers[0]["field_id"] == "salary"
            assert answers[0]["save_for_reuse"] and answers[0]["user_confirmed"]
            app["fields"][0].update(value=answers[0]["value"], user_confirmed=True, value_source="user")
            app.update(status="ready_for_review", missing_fields=[], readiness_score=1)
            data = app
        elif path.endswith("/review"):
            app.update(review_token="a" * 64); data = app
        else:
            unexpected.append(path); await route.abort(); return
        await route.fulfill(json={"data": copy.deepcopy(data), "error": None})
    async with async_playwright() as driver:
        browser = await driver.chromium.launch(headless=True, executable_path=os.environ.get("BROWSER_EXECUTABLE_PATH"))
        try:
            context = await browser.new_context(service_workers="block", viewport={"width": 390, "height": 844})
            await context.route("**/*", intercept)
            page = await context.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            await page.goto(url + "/applications/required-only")
            salary = page.get_by_label("Expectation Salary per annum", exact=False)
            await salary.wait_for()
            assert await page.get_by_label("Optional cover letter", exact=False).count() == 0
            assert await page.get_by_label("Optional AI suggestion", exact=False).count() == 0
            assert await page.get_by_label("I explicitly confirm this AI suggestion is accurate.").count() == 0
            await page.get_by_text("Currency: not specified by employer.", exact=False).wait_for()
            assert await salary.get_attribute("aria-describedby")
            output.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(output / "salary-guidance-mobile.png"), full_page=True)
            await salary.fill("INR 1200000/year")
            await page.get_by_role("button", name="Save answers", exact=True).click()
            await page.get_by_text("Application updated.", exact=True).wait_for()
            await page.get_by_role("button", name="Prepare final review", exact=True).click()
            await page.get_by_role("button", name="Approve & submit application", exact=True).wait_for()
            assert not unexpected and not errors
            assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
            output.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(output / "required-only-mobile.png"), full_page=True)
            result = {"checks": ["optional empty and AI fields hidden", "salary currency/period guidance accessible", "required answers only saved", "review without optional confirmation", "mobile layout and individual approval"],
                "requests_intercepted": len(requests), "unexpected_requests": unexpected, "page_errors": errors}
            (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(json.dumps(result))
        finally:
            await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:13000")
    parser.add_argument("--output", type=Path, default=Path(".verification/required-questions-ui"))
    args = parser.parse_args()
    asyncio.run(main(args.url.rstrip("/"), args.output))
