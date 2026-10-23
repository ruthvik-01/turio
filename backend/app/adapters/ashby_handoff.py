"""Isolated visible browser lifetime. Review payload stays in process memory."""
import asyncio
import base64
import json
import sys
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from app.adapters import ashby_hosted
from app.adapters.ashby import AshbyAdapter
from app.core.config import get_settings
from app.core.errors import AppError


async def confirm_fill():
    print(json.dumps({"inspected": True}), flush=True)
    return await asyncio.to_thread(sys.stdin.buffer.readline) == b"fill\n"


async def main(payload):
    settings = get_settings()
    AshbyAdapter(None).check_url(payload["url"])
    async with async_playwright() as driver:
        browser = None
        try:
            async with asyncio.timeout(settings.browser_timeout_seconds):
                browser = await driver.chromium.launch(headless=False, executable_path=settings.browser_executable_path)
                closed = asyncio.Event()
                browser.on("disconnected", closed.set)
                context = await browser.new_context(service_workers="block", accept_downloads=False)
                page = await context.new_page()
                page.set_default_timeout(15000)
                async def guard(route):
                    if route.request.method in {"GET", "HEAD", "OPTIONS"} or ashby_hosted.public_read(route.request, payload["url"]):
                        await route.fallback()
                    else:
                        await route.abort()
                await context.route("**/*", guard)
                ashby_hosted.bind_metadata(page, payload["url"])
                await page.goto(payload["url"], wait_until="domcontentloaded")
                await page.locator(".ashby-application-form-submit-button").wait_for(state="visible")
                AshbyAdapter(None).check_url(page.url)
                if urlparse(page.url).path.strip("/").split("/")[:2] != urlparse(payload["url"]).path.strip("/").split("/")[:2]:
                    raise AppError("CONFLICT", "The employer page redirected to a different posting.", 409)
                # Recheck before releasing approved data to this employer page.
                from app.ml.scoring import digest
                if digest(await ashby_hosted.schema(page)) != digest(payload["snapshot"]["schema"]):
                    raise AppError("CONFLICT", "The employer form changed. Prepare and review again.", 409)
                if not await confirm_fill():
                    raise AppError("SUBMISSION_NOT_APPROVED", "Browser filling was not authorized.", 409)
                await context.unroute("**/*", guard)
                resume = payload.get("resume")
                upload = {"name": resume["name"], "mimeType": "application/pdf", "buffer": base64.b64decode(resume["buffer"])} if resume else None
                manual = await ashby_hosted.fill(page, payload["snapshot"], upload)
                await page.bring_to_front()
                print(json.dumps({"ready": True, "manual_fields": manual}), flush=True)
                payload.clear()
            # ponytail: one short-lived browser per approved handoff; no persisted session/profile.
            try:
                await asyncio.wait_for(closed.wait(), 15 * 60)
            except asyncio.TimeoutError:
                pass
        except AppError as exc:
            print(json.dumps({"ready": False, "code": exc.code, "message": exc.message}), flush=True)
        except Exception:
            print(json.dumps({"ready": False, "code": "BROWSER_ACTION_FAILED", "message": "The visible browser could not be prepared. Review and try again."}), flush=True)
        finally:
            if browser and browser.is_connected():
                await browser.close()


if __name__ == "__main__":
    asyncio.run(main(json.loads(sys.stdin.buffer.readline())))
