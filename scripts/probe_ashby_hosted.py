"""Read-only hosted Ashby probe: no candidate data or submission requests."""
import asyncio
import json
from urllib.parse import urlparse

from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as driver:
        browser = await driver.chromium.launch(headless=True)
        page = await browser.new_page()
        reads = []

        async def response_data(response):
            if "op=ApiJobPosting" in response.url:
                data = await response.json()
                print("FORM_METADATA", json.dumps(data.get("data", {}).get("jobPosting", {}).get("applicationForm")))
        page.on("response", response_data)

        async def guard(route):
            request = route.request
            parsed = urlparse(request.url)
            if request.method in {"GET", "HEAD", "OPTIONS"}:
                await route.continue_()
                return
            try:
                body = request.post_data_json
            except Exception:
                body = {}
            operation = body.get("operationName") if isinstance(body, dict) else None
            reads.append({"url": request.url, "operation": operation, "keys": list(body) if isinstance(body, dict) else []})
            if parsed.hostname == "jobs.ashbyhq.com" and operation in {"ApiJobPosting", "ApiOrganizationFromHostedJobsPageName"}:
                print("PUBLIC_READ", json.dumps(body))
                await route.continue_()
            else:
                await route.abort()

        await page.route("**/*", guard)
        await page.goto("https://jobs.ashbyhq.com/0x/c6510c38-a082-4d6b-8872-4645071543f3/application")
        try:
            await page.get_by_text("Submit Application", exact=True).wait_for(timeout=20000)
        except Exception:
            pass
        print("DOM", json.dumps(await page.locator("body").evaluate("""el => ({text:el.innerText.slice(-14000), controls:[...el.querySelectorAll('input,textarea,select,button')].map(e=>({tag:e.tagName,type:e.type,id:e.id,name:e.name,role:e.getAttribute('role'),required:e.required,aria:e.getAttribute('aria-label'),label:[...(e.labels||[])].map(l=>l.innerText),outer:e.outerHTML.slice(0,900)}))})""")))
        print("REQUESTS", json.dumps(reads))
        print("WRAPPERS", await page.locator("#_systemfield_name").evaluate("el=>el.parentElement.parentElement.outerHTML.slice(0,1500)"))
        print("LOCATION", await page.get_by_role("combobox").evaluate("el=>el.parentElement.parentElement.parentElement.outerHTML.slice(0,2200)"))
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
