"""Conservative native-control Ashby adapter; experimental until live verification.

No free-form agent can submit. Browser Use owns an isolated browser; Playwright
performs only explicit inspected-control operations on the reviewed snapshot.
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from app.core.config import get_settings
from app.core.errors import AppError
from app.ml.scoring import digest
from app.adapters.native_submission import FileProof, SubmissionPermit

logger = logging.getLogger(__name__)

TRIAL_COMPANIES = {"1password", "linear", "supabase", "vercel", "notion"}
CONFIRMATION = r"application (has been )?(submitted|received)|thank you for applying"

INSPECT_FORM = r"""() => {
  const visible = el => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  if (document.characterSet.toLowerCase() !== 'utf-8')
    return {error: "Only UTF-8 native forms are supported."};
  if (document.querySelector('iframe[src*="captcha"], [class*="captcha"]'))
    return {error: "CAPTCHA requires manual completion."};
  const buttons = [...document.querySelectorAll('button,input[type="submit"]')].filter(el =>
    visible(el) && /^(submit application|submit)$/i.test((el.innerText || el.value || '').trim()));
  if (buttons.length !== 1 || !buttons[0].form)
    return {error: "A unique native form submission button is required."};
  const b = buttons[0], form = b.form;
  if ([...form.querySelectorAll('[role="combobox"]:not(select), [role="radiogroup"], input[type="radio"], [role="checkbox"]:not(input), [contenteditable="true"]')].some(visible))
    return {error: "This form contains controls outside the native-control adapter."};
  const controls = [...form.elements].filter(el => ['INPUT','SELECT','TEXTAREA'].includes(el.tagName) &&
    !el.disabled && !['submit','button','reset'].includes(el.type));
  const labelText = label => {
    const clone = label.cloneNode(true);
    clone.querySelectorAll('input,select,textarea,button').forEach(el => el.remove());
    return clone.textContent.replace(/\s+/g, ' ').trim();
  };
  const fields = [];
  for (const el of controls) {
    const type = el.tagName === 'SELECT' ? 'select' : el.tagName === 'TEXTAREA' ? 'textarea' : el.type;
    if (!['text','email','tel','url','number','checkbox','file','select','textarea'].includes(type) ||
        (type !== 'file' && !visible(el)) || el.multiple)
      return {error: "Hidden, multiple or unsupported controls require a separately audited adapter."};
    const label = [...(el.labels || [])].map(labelText).join(' ') || el.getAttribute('aria-label');
    if (!label || !el.name) return {error: "An input has no stable label or submission name."};
    const locator = el.id ? '#' + CSS.escape(el.id) : el.tagName.toLowerCase() + '[name="' + CSS.escape(el.name) + '"]';
    if (document.querySelectorAll(locator).length !== 1) return {error: "An input locator is ambiguous."};
    fields.push({field_key: el.id || el.name, label: label.replace(/\s*\*\s*$/, '').trim(),
      name: el.name, checkbox_value: type === 'checkbox' ? el.value : null,
      input_type: type, required: el.required || el.getAttribute('aria-required') === 'true',
      source_locator: locator, options: type === 'select' ? [...el.options].filter(o => o.value).map(o => ({value: o.value, label: o.text})) : []});
  }
  if (fields.length === 0 || fields.length > 100 || new Set(fields.map(f => f.name)).size !== fields.length ||
      (b.name && fields.some(f => f.name === b.name)))
    return {error: "The form must have bounded, unique submission field names."};
  const submit_locator = b.id ? '#' + CSS.escape(b.id) : b.tagName === 'INPUT' ? 'input[type="submit"]' : 'button[type="submit"]';
  if (document.querySelectorAll(submit_locator).length !== 1) return {error: "Submission control is ambiguous."};
  const form_method = (b.getAttribute('formmethod') || form.method).toLowerCase();
  const destination = new URL(b.hasAttribute('formaction') ? b.formAction : form.action);
  destination.hash = '';
  const form_action = destination.href;
  const form_enctype = b.getAttribute('formenctype') || form.enctype;
  if (form_method !== 'post' || !['multipart/form-data','application/x-www-form-urlencoded'].includes(form_enctype) ||
      (fields.some(f => f.input_type === 'file') && form_enctype !== 'multipart/form-data'))
    return {error: "Only explicit native POST form transports are supported."};
  return {version: 'native-form-v2', fields, submit_locator, form_method, form_action, form_enctype,
          submit_name: b.name || null, submit_value: b.value || ''};
}"""


class AshbyAdapter:
    def __init__(self, load_resume, authorize=None):
        self.load_resume = load_resume
        self.authorize = authorize

    def check_url(self, url):
        if not get_settings().browser_automation_enabled:
            raise AppError("UNSUPPORTED_APPLICATION", "Browser assistance is disabled. You can open the employer site and track a manual application.", 409)
        try:
            parts = urlparse(url)
            port = parts.port
        except ValueError as exc:
            raise AppError("UNSUPPORTED_APPLICATION", "The application URL is invalid.", 422) from exc
        company = parts.path.strip("/").split("/")[0].casefold()
        if parts.scheme != "https" or parts.hostname != "jobs.ashbyhq.com" or port not in {None, 443} or parts.username or parts.password or company not in TRIAL_COMPANIES:
            raise AppError("UNSUPPORTED_APPLICATION", "This URL is outside the experimental Ashby trial allowlist. Continue manually.", 422)

    @asynccontextmanager
    async def page(self, url):
        self.check_url(url)
        os.environ.setdefault("ANONYMIZED_TELEMETRY", "false")
        try:
            from browser_use import Browser
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise AppError("BROWSER_ACTION_FAILED", "Install the optional browser dependencies and Chromium first.", 503) from exc
        settings = get_settings()
        browser = Browser(headless=settings.browser_headless, executable_path=settings.browser_executable_path,
                          enable_default_extensions=False, allowed_domains=["jobs.ashbyhq.com"],
                          keep_alive=False)
        playwright = None
        context = None
        connection = None
        try:
            async with asyncio.timeout(settings.browser_timeout_seconds):
                await browser.start()
                playwright = await async_playwright().start()
                connection = await playwright.chromium.connect_over_cdp(browser.cdp_url)
                context = await connection.new_context(service_workers="block", accept_downloads=False)
                page = await context.new_page()
                page.set_default_timeout(15000)
                allowed = {"jobs.ashbyhq.com", "app.ashbyhq.com", "assets.ashbyhq.com", "fonts.googleapis.com", "fonts.gstatic.com"}
                gate = {"approved": False, "sealed": False, "permit": None,
                        "authorize": None, "lock": asyncio.Lock()}

                async def guard(route):
                    request = route.request
                    parsed = urlparse(request.url)
                    if parsed.scheme != "https" or parsed.hostname not in allowed or parsed.username or parsed.password or parsed.port not in {None, 443}:
                        await route.abort()
                    elif request.method not in {"GET", "HEAD", "OPTIONS"}:
                        async with gate["lock"]:
                            permit = gate["permit"]
                            if gate["approved"] and permit and gate["authorize"] and not permit.consumed and not permit.rejected:
                                try:
                                    await gate["authorize"]()
                                    allowed_post = permit.allow(request)
                                except Exception:
                                    permit.rejected = True
                                    allowed_post = False
                            else:
                                if permit and gate["approved"]:
                                    permit.rejected = True
                                allowed_post = False
                            if allowed_post:
                                await route.fallback()
                            else:
                                await route.abort()
                    elif gate["sealed"]:
                        # Once candidate values enter the page, no read/beacon
                        # request can carry them out before/around submission.
                        await route.abort()
                    else:
                        # Preserve earlier terminal interceptors used by isolated
                        # local tests; without one this continues to the network.
                        await route.fallback()

                # Fail closed before approval, including scripts/autosubmit.
                # Sites needing pre-submit POST uploads/read RPCs require a
                # separately audited transport adapter, not a relaxed gate.
                await context.route("**/*", guard)
                async def block_websocket(websocket):
                    await websocket.close()
                await context.route_web_socket("**/*", block_websocket)
                await page.goto(url, wait_until="domcontentloaded")
                yield page, gate
        except AppError:
            raise
        except Exception as exc:
            raise AppError("BROWSER_ACTION_FAILED", "Browser assistance stopped. No successful submission is claimed; continue manually or inspect the application event.", 503) from exc
        finally:
            was_error = sys.exc_info()[0] is not None
            cleanup_errors = []
            for name, resource, method in (("context", context, "close"), ("connection", connection, "close"),
                                           ("browser", browser, "kill"), ("playwright", playwright, "stop")):
                if resource is None:
                    continue
                try:
                    await asyncio.wait_for(getattr(resource, method)(), timeout=10)
                except Exception:
                    cleanup_errors.append(name)
            if cleanup_errors:
                logger.warning("browser_cleanup_failed", extra={"extra_fields": {"resources": cleanup_errors}})
                if not was_error:
                    raise AppError("BROWSER_ACTION_FAILED", "Browser cleanup failed; no successful operation is claimed.", 503)

    async def schema(self, page):
        result = await page.evaluate(INSPECT_FORM)
        if result.get("error"):
            raise AppError("UNSUPPORTED_APPLICATION", result["error"], 422)
        if len({f["field_key"] for f in result["fields"]}) != len(result["fields"]):
            raise AppError("UNSUPPORTED_APPLICATION", "Form field identities are ambiguous.", 422)
        self.check_url(result["form_action"])
        if urlparse(result["form_action"]).path.strip("/").split("/")[0] != urlparse(page.url).path.strip("/").split("/")[0]:
            raise AppError("UNSUPPORTED_APPLICATION", "The form submits to a different company.", 422)
        return result

    async def inspect(self, url):
        async with self.page(url) as (page, _):
            return await self.schema(page)

    async def verify_values(self, page, snapshot, observed, files):
        for field in observed["fields"]:
            value = snapshot["answers"].get(field["field_key"])
            locator = page.locator(field["source_locator"])
            if field["input_type"] == "file":
                actual = await locator.evaluate("""async el => {
                  if (!el.files.length) return null;
                  if (el.files.length !== 1) return {invalid: true};
                  const file = el.files[0], hash = await crypto.subtle.digest('SHA-256', await file.arrayBuffer());
                  return {name:file.name, size:file.size, hash:[...new Uint8Array(hash)].map(x=>x.toString(16).padStart(2,'0')).join('')};
                }""")
                expected = files[field["name"]]
                valid = (actual is None and not value) or (actual and actual.get("name") == expected.filename and actual.get("size") == expected.size and actual.get("hash") == expected.checksum)
            elif field["input_type"] == "checkbox":
                valid = await locator.is_checked() == bool(value)
            else:
                valid = await locator.input_value() == (value or "")
            if not valid:
                raise AppError("BROWSER_ACTION_FAILED", "A filled value differs from the reviewed answer.", 409)

    async def fill_page(self, page, snapshot, gate):
        observed = await self.schema(page)
        if digest(observed) != digest(snapshot["schema"]):
            raise AppError("CONFLICT", "The employer form changed. Prepare and review it again.", 409)
        if set(snapshot["answers"]) - {f["field_key"] for f in observed["fields"]}:
            raise AppError("CONFLICT", "The review contains unknown fields.", 409)
        gate["sealed"] = True
        fields, files = {}, {}
        for field in observed["fields"]:
            value = snapshot["answers"].get(field["field_key"])
            if field["required"] and (value is None or value == "" or (field["input_type"] == "checkbox" and value is not True)):
                raise AppError("MISSING_REQUIRED_FIELD", "A required field has no approved value.", 422)
            if field["input_type"] == "checkbox":
                if value is not None and not isinstance(value, bool):
                    raise AppError("CONFLICT", "A checkbox answer must be boolean.", 422)
                if value:
                    fields[field["name"]] = field["checkbox_value"]
            elif value is not None and not isinstance(value, str):
                raise AppError("CONFLICT", "This form field requires text.", 422)
            elif field["input_type"] != "file":
                fields[field["name"]] = value or ""
            locator = page.locator(field["source_locator"])
            upload = None
            if field["input_type"] == "file":
                if value and value != snapshot["resume_id"]:
                    raise AppError("FORBIDDEN", "Only the reviewed original resume can be uploaded.", 403)
                if value:
                    name, content = await self.load_resume(value)
                    files[field["name"]] = FileProof.from_bytes(name, content)
                    upload = {"name": name, "mimeType": "application/pdf", "buffer": content}
                else:
                    files[field["name"]] = FileProof.from_bytes("", b"", "application/octet-stream")
            # Bounded retries for idempotent fill only. Never retry submission.
            for attempt in range(3):
                try:
                    if field["input_type"] == "file":
                        await locator.set_input_files(upload or [])
                    elif field["input_type"] == "checkbox":
                        await locator.set_checked(bool(value))
                    elif field["input_type"] == "select":
                        await locator.select_option(value or "")
                    else:
                        await locator.fill(value or "")
                    break
                except Exception:
                    if attempt == 2:
                        raise
        await self.verify_values(page, snapshot, observed, files)
        valid = await page.locator(observed["submit_locator"]).evaluate("(button) => button.form.checkValidity()")
        if not valid:
            raise AppError("MISSING_REQUIRED_FIELD", "The employer form rejected one or more values.", 422)
        if observed["submit_name"]:
            fields[observed["submit_name"]] = observed["submit_value"]
        return observed, SubmissionPermit(observed["form_action"], fields, files)

    async def fill(self, url, snapshot):
        async with self.page(url) as (page, gate):
            await self.fill_page(page, snapshot, gate)

    async def submit(self, url, snapshot):
        if self.authorize is None:
            raise AppError("SUBMISSION_NOT_APPROVED", "No submission authorization boundary is configured.", 409)
        async with self.page(url) as (page, gate):
            observed, permit = await self.fill_page(page, snapshot, gate)
            before = await page.locator("body").inner_text()
            successful_posts = []
            page.on("response", lambda response: successful_posts.append(response.status)
                    if response.request == permit.request and 200 <= response.status < 300 else None)
            # Recheck persisted authorization immediately before the one click.
            await self.authorize(snapshot)
            if digest(await self.schema(page)) != digest(observed):
                raise AppError("CONFLICT", "The form changed during authorization.", 409)
            await self.verify_values(page, snapshot, observed, permit.files)
            gate["permit"] = permit
            gate["authorize"] = lambda: self.authorize(snapshot)
            gate["approved"] = True
            await page.locator(observed["submit_locator"]).click()
            # A click alone is not success. Require changed confirmation text,
            # a successful server response and disappearance of the input form.
            await page.wait_for_function(
                r"""([before, pattern]) => document.body.innerText !== before &&
                new RegExp(pattern, 'i').test(document.body.innerText) &&
                ![...document.querySelectorAll('input[required],textarea[required],select[required]')].some(e => e.offsetWidth || e.offsetHeight)""",
                arg=[before, CONFIRMATION], timeout=15000)
            verified = bool(successful_posts) and permit.consumed and not permit.rejected
            return {"verified": verified, "confirmation": "Confirmation displayed after the single reviewed POST." if verified else "Submission not verified.",
                    "form_schema_version": observed["version"], "adapter_version": "ashby-native-v2"}
