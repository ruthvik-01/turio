"""Real loopback signup/login/logout smoke; no mocked auth or employer/model calls.
Creates one synthetic local account; credentials remain in memory and are not printed.
"""
import argparse
import asyncio
import json
import secrets
import uuid
from urllib.parse import urlparse
from playwright.async_api import async_playwright


async def main(base):
    origin = urlparse(base)
    assert origin.hostname in {"localhost", "127.0.0.1"}
    email = f"turio-auth-check-{uuid.uuid4().hex}@example.com"
    password = secrets.token_urlsafe(24)
    checks = []

    def check(name, passed):
        assert passed, name
        checks.append(name)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()

        async def guard(route):
            target = urlparse(route.request.url)
            if target.netloc != origin.netloc:
                await route.abort()
            elif target.path.startswith("/api/") and not target.path.startswith("/api/auth/"):
                await route.fulfill(status=503, json={"data": None, "error": {"code": "AUTH_SMOKE_ONLY", "message": "Non-auth requests excluded from this smoke check"}})
            else:
                await route.continue_()

        await context.route("**/*", guard)
        page = await context.new_page()
        await page.goto(base + "/signup")
        await page.get_by_label("Email address", exact=True).fill(email)
        await page.get_by_label("Password", exact=True).fill(password)
        async with page.expect_response(lambda r: r.url.endswith("/api/auth/register") and r.request.method == "POST") as pending:
            await page.locator("form button[type=submit]").click()
        response = await pending.value
        check("real signup 201", response.status == 201)
        result = await response.json()
        check("token omitted from browser JSON", "token" not in result["data"])
        user_id = result["data"]["user"]["id"]
        await page.get_by_role("button", name="Sign out", exact=True).wait_for()
        cookies = {c["name"]: c for c in await context.cookies()}
        check("HttpOnly session cookies", all(n in cookies and cookies[n]["httpOnly"] and cookies[n]["sameSite"] == "Lax" for n in ["turio_access", "turio_refresh"]))
        me = await context.request.get(base + "/api/auth/me")
        check("authenticated identity", me.status == 200 and (await me.json())["data"]["id"] == user_id)
        async with page.expect_response(lambda r: r.url.endswith("/api/auth/logout")) as pending:
            await page.get_by_role("button", name="Sign out", exact=True).click()
        check("real logout 200", (await pending.value).status == 200)
        check("signed out identity 401", (await context.request.get(base + "/api/auth/me")).status == 401)
        check("cookies cleared", not {c["name"] for c in await context.cookies()} & {"turio_access", "turio_refresh"})
        await page.goto(base + "/login")
        await page.get_by_label("Email address", exact=True).fill(email)
        await page.get_by_label("Password", exact=True).fill(password + "-wrong")
        async with page.expect_response(lambda r: r.url.endswith("/api/auth/login")) as pending:
            await page.locator("form button[type=submit]").click()
        check("wrong password 401", (await pending.value).status == 401)
        await page.get_by_label("Password", exact=True).fill(password)
        async with page.expect_response(lambda r: r.url.endswith("/api/auth/login")) as pending:
            await page.locator("form button[type=submit]").click()
        check("real login form 200", (await pending.value).status == 200)
        await page.get_by_role("button", name="Sign out", exact=True).wait_for()
        me = await context.request.get(base + "/api/auth/me")
        check("login restored same identity", me.status == 200 and (await me.json())["data"]["id"] == user_id)
        async with page.expect_response(lambda r: r.url.endswith("/api/auth/logout")) as pending:
            await page.get_by_role("button", name="Sign out", exact=True).click()
        check("final logout 200", (await pending.value).status == 200)
        check("final signed out 401", (await context.request.get(base + "/api/auth/me")).status == 401)
        await browser.close()
    print(json.dumps({"passed": len(checks), "failed": 0, "checks": checks,
        "scope": "Real local auth only; one synthetic account retained, no credentials printed"}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:13002")
    asyncio.run(main(parser.parse_args().url.rstrip("/")))
