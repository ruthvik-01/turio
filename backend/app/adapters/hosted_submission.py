"""Approved Ashby form-state RPCs, original-file upload and one final action.

Queries are pinned from public frontend 5da946847bf97ca3d47371b9c5dca6f548db144a.
The site's normal reCAPTCHA flow runs unchanged; challenges are never solved here.
"""
import asyncio
import base64
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from app.adapters.native_submission import FileProof, SubmissionPermit
from app.core.errors import AppError
from app.ml.scoring import digest

QUERIES = json.loads(Path(__file__).with_name("ashby_mutations.json").read_text(encoding="utf-8"))
TRANSPORT = "ashby-hosted-v2"
SUPPORTED_TYPES = {"String", "LongText", "Email", "Phone", "Url", "Number", "Boolean", "ValueSelect", "Location", "File"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def json_equal(left, right):
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isfinite(left) and math.isfinite(right) and left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(json_equal(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(json_equal(a, b) for a, b in zip(left, right))
    return left == right


def request_body(request):
    if request.method != "POST" or request.headers.get("content-type", "").split(";", 1)[0] != "application/json":
        raise ValueError("Unexpected transport")
    raw = request.post_data_buffer or b""
    if len(raw) > 256 * 1024:
        raise ValueError("Oversized RPC")
    return json.loads(raw, object_pairs_hook=unique_object)


@dataclass
class JsonPermit:
    action: str
    body: dict
    consumed: bool = False
    rejected: bool = False
    request: object | None = None

    def allow(self, request):
        try:
            if self.consumed or self.rejected or request.url != self.action or not json_equal(request_body(request), self.body):
                raise ValueError("RPC differs from review")
        except (ValueError, TypeError, UnicodeError):
            self.rejected = True
            return False
        self.consumed, self.request = True, request
        return True


def query_tokens(query):
    # Token comparison preserves word boundaries; whitespace/comma formatting is irrelevant.
    if not isinstance(query, str) or len(query) > 100000:
        raise ValueError("Invalid query")
    pattern = r"\.\.\.|[_A-Za-z][_0-9A-Za-z]*|[!$():{}\[\]@]"
    if re.sub(pattern, "", query).strip(" \t\r\n,"):
        raise ValueError("Unpinned query syntax")
    return re.findall(pattern, query)


class FinalPermit(JsonPermit):
    def __init__(self, url, forms, notice_id=None):
        company, posting = urlparse(url).path.strip("/").split("/")[:2]
        main = forms[0]
        self.operation = "ApiSubmitMultipleFormsAction" if len(forms) > 1 else "ApiSubmitSingleApplicationFormAction"
        variables = {"organizationHostedJobsPageName": company, "jobPostingId": posting}
        if len(forms) == 1:
            variables.update(formRenderIdentifier=main["id"], formDefinitionIdentifier=main.get("sourceFormDefinitionId"),
                             actionIdentifier=main["formControls"][0]["identifier"])
        else:
            variables.update(applicationFormRenderIdentifier=main["id"],
                             applicationFormDefinitionIdentifier=main.get("sourceFormDefinitionId"),
                             applicationFormActionIdentifier=main["formControls"][0]["identifier"],
                             surveyIdentifiers=[{"formRenderId": f["id"], "actionIdentifier": f["formControls"][0]["identifier"],
                                                 "sourceFormDefinitionId": f.get("sourceFormDefinitionId")} for f in forms[1:]])
        self.variables = variables
        self.notice_id = notice_id
        super().__init__(f"https://jobs.ashbyhq.com/api/non-user-graphql?op={self.operation}", {})

    def allow(self, request):
        try:
            body = request_body(request)
            variables = body["variables"]
            extras = {"recaptchaToken", "sourceAttributionCode", "viewedAutomatedProcessingLegalNoticeRuleId",
                      "deviceFingerprint", "applicationRequestId"}
            if (self.consumed or self.rejected or request.url != self.action or set(body) != {"operationName", "query", "variables"}
                or body["operationName"] != self.operation or query_tokens(body["query"]) != query_tokens(QUERIES[self.operation])
                or not set(self.variables) <= set(variables) or set(variables) - (set(self.variables) | extras)
                or any(variables.get(key) != value for key, value in self.variables.items())
                or variables.get("sourceAttributionCode") not in {None, ""}
                or variables.get("viewedAutomatedProcessingLegalNoticeRuleId") != self.notice_id
                or not isinstance(variables.get("recaptchaToken"), str) or not 1 <= len(variables["recaptchaToken"]) <= 16000
                or variables.get("applicationRequestId") is not None
                or any(value is not None and (not isinstance(value, str) or len(value) > 4096)
                       for value in (variables.get("deviceFingerprint"),))):
                raise ValueError("Final action differs from approval")
        except (ValueError, TypeError, KeyError, UnicodeError):
            self.rejected = True
            return False
        self.consumed, self.request = True, request
        return True


def trusted_upload(url):
    try:
        target = urlparse(url)
        return bool(target.scheme == "https" and not target.username and not target.password and target.port in {None, 443}
                    and re.fullmatch(r"(?:[a-z0-9][a-z0-9.-]*\.)?s3(?:[.-][a-z0-9-]+)?\.amazonaws\.com", target.hostname or ""))
    except ValueError:
        return False


def recaptcha_request(request):
    try:
        target = urlparse(request.url)
        return (target.scheme == "https" and target.port in {None, 443} and not target.username and not target.password
                and target.hostname in {"www.google.com", "www.recaptcha.net", "www.gstatic.com"}
                and target.path.startswith("/recaptcha/"))
    except ValueError:
        return False


async def rpc(page, gate, authorize, operation, variables):
    await authorize()
    body = {"operationName": operation, "query": QUERIES[operation], "variables": variables}
    permit = JsonPermit(f"https://jobs.ashbyhq.com/api/non-user-graphql?op={operation}", body)
    gate.update(permit=permit, approved=True, sealed=True, authorize=authorize, hosted=True)
    result = await page.evaluate("""async ({url, body}) => {
      const response=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      const text=await response.text();
      if(text.length>2000000) throw Error('Oversized form response');
      return {ok:response.ok,data:JSON.parse(text)};
    }""", {"url": permit.action, "body": body})
    if not permit.consumed or permit.rejected or not result["ok"] or result["data"].get("errors"):
        raise AppError("BROWSER_ACTION_FAILED", "The employer did not accept an approved form update. No submission is verified.", 409)
    return result["data"].get("data", {})


async def location_value(page, gate, authorize, field, value):
    data = await rpc(page, gate, authorize, "ApiAutocompleteGeoLocation", {"text": value, "locationTypes": field.get("location_types")})
    suggestions = data.get("result", {}).get("suggestions", [])
    words = set(re.findall(r"[a-z0-9]+", value.casefold()))
    exact = [s for s in suggestions if s.get("name", "").casefold().strip() == value.casefold().strip()]
    matches = exact or [s for s in suggestions if words and words <= set(re.findall(r"[a-z0-9]+", s.get("name", "").casefold()))]
    if len(matches) != 1 or not matches[0].get("geoLocationPath"):
        raise AppError("MISSING_REQUIRED_FIELD", "Your location has no unique employer match. Use a complete city, region and country, or continue manually.", 422)
    selected = matches[0]
    provider_id = selected["geoLocationPath"][-1].get("providerLocationId")
    if not isinstance(provider_id, str) or not provider_id:
        raise AppError("UNSUPPORTED_APPLICATION", "The employer's location format is unsupported. Continue manually.", 422)
    return {"text": selected["name"], "providerLocationId": provider_id}


def scalar_value(field, value):
    kind = field["hosted_type"]
    if kind == "Boolean":
        if value not in {"true", "false"}:
            raise AppError("MISSING_REQUIRED_FIELD", "Confirm yes or no for the employer question.", 422)
        return value == "true"
    if kind == "MultiValueSelect":
        if isinstance(value, bool) and len(field["selectable_values"]) == 1:
            return [field["selectable_values"][0]["value"]] if value else []
        if not isinstance(value, list) or len(set(value)) != len(value) or not set(value) <= {o["value"] for o in field["selectable_values"]}:
            raise AppError("MISSING_REQUIRED_FIELD", "Choose available employer options.", 422)
        return value
    if kind == "ValueSelect":
        option = next((o for o in field["options"] if o["value"] == value), None)
        choices = [o for o in field["selectable_values"] if option and o.get("label") == option["label"]]
        if len(choices) != 1:
            raise AppError("UNSUPPORTED_APPLICATION", "The reviewed employer option is ambiguous.", 422)
        return choices[0]["value"]
    if kind == "Number":
        try:
            number = float(value)
            if not math.isfinite(number) or abs(number) > 9007199254740991:
                raise ValueError()
            return number
        except (ValueError, TypeError):
            raise AppError("MISSING_REQUIRED_FIELD", "The employer requires a finite number.", 422) from None
    if kind not in SUPPORTED_TYPES or not isinstance(value, str):
        raise AppError("UNSUPPORTED_APPLICATION", "This employer field requires manual completion.", 422)
    return value


def audit_forms(original, current, expected):
    def entries(forms):
        return {e["field"]["path"]: e for f in forms for s in f.get("sections", []) for e in s.get("fieldEntries", [])}

    def contract(forms):
        return [{"id": f["id"], "definition": f.get("sourceFormDefinitionId"), "controls": f.get("formControls"),
                 "sections": [{"hidden": s.get("isHidden"), "fields": [
                     {"field": {k: e["field"].get(k) for k in ("path", "type", "title", "humanReadablePath", "isMany", "selectableValues", "locationTypes")},
                      "required": e.get("isRequired"), "hidden": e.get("isHidden"), "help": e.get("descriptionHtml")}
                     for e in s.get("fieldEntries", [])]} for s in f.get("sections", [])]} for f in forms]

    if digest(contract(original)) != digest(contract(current)):
        raise AppError("CONFLICT", "The employer changed the form during preparation. Submission stopped.", 409)
    before, after = entries(original), entries(current)
    for key, entry in after.items():
        received = entry.get("fieldValue") or {}
        if key in expected:
            wanted = expected[key]
            if any(not json_equal(received.get(k), v) for k, v in wanted.items()):
                raise AppError("CONFLICT", "An employer-stored answer or resume changed after verification. Submission stopped.", 409)
        elif entry.get("isHidden"):
            if digest(received) != digest(before[key].get("fieldValue") or {}):
                raise AppError("CONFLICT", "An unreviewed hidden employer value changed. Submission stopped.", 409)
        else:
            value = received.get("value")
            baseline = (before[key].get("fieldValue") or {}).get("value")
            blank = value is None or (value is False and baseline is False) or value == "" or value == [] or value == {}
            if not blank or received.get("id") or received.get("files"):
                raise AppError("CONFLICT", "The employer populated an answer you did not approve. Submission stopped.", 409)


async def upload(page, gate, authorize, company, filename, original):
    data = await rpc(page, gate, authorize, "ApiCreateFileUploadHandle", {
        "organizationHostedJobsPageName": company, "fileUploadContext": "NonUserFormEngine",
        "filename": filename, "contentType": "application/pdf", "contentLength": len(original)})
    handle = data.get("fileUploadHandle") or {}
    fields, url = handle.get("fields"), handle.get("url")
    if (not isinstance(fields, dict) or not fields or len(fields) > 25 or not trusted_upload(url or "")
        or not isinstance(handle.get("handle"), str) or not handle["handle"]
        or any(not isinstance(k, str) or not isinstance(v, str) for k, v in fields.items())
        or "file" in fields or "Content-Type" in fields):
        raise AppError("UNSUPPORTED_APPLICATION", "The employer upload destination or policy is unsupported.", 422)
    permit = SubmissionPermit(url, {"Content-Type": "application/pdf", **fields}, {"file": FileProof.from_bytes(filename, original)})
    permit.external_upload = True
    gate.update(permit=permit, authorize=authorize)
    await authorize()
    ok = await page.evaluate("""async ({url,fields,name,bytes}) => {
      const data=new FormData();data.append('Content-Type','application/pdf');
      for(const [key,value] of Object.entries(fields))data.append(key,value);
      const raw=Uint8Array.from(atob(bytes),c=>c.charCodeAt(0));
      data.append('file',new File([raw],name,{type:'application/pdf'}));
      return (await fetch(url,{method:'POST',body:data})).ok;
    }""", {"url": url, "fields": fields, "name": filename, "bytes": base64.b64encode(original).decode()})
    if not ok or not permit.consumed or permit.rejected:
        raise AppError("BROWSER_ACTION_FAILED", "The approved original PDF upload was not accepted.", 409)
    return handle["handle"]


async def submit(adapter, page, gate, url, snapshot):
    from app.adapters import ashby_hosted

    observed = await ashby_hosted.schema(page)
    if not ashby_hosted.automatic_supported(observed) or digest(observed) != digest(snapshot["schema"]):
        raise AppError("CONFLICT", "The employer form changed or cannot be submitted automatically. Prepare and review again.", 409)
    forms = page._turio_hosted_forms
    current = list(forms)
    expected = {}
    company = urlparse(url).path.strip("/").split("/")[0]
    answers = snapshot["answers"]
    fields = {f["field_key"]: f for f in observed["fields"]}
    if set(answers) - set(fields) or any(f["required"] and f["field_key"] not in answers for f in fields.values()):
        raise AppError("MISSING_REQUIRED_FIELD", "The approved snapshot does not contain all required answers.", 422)
    authorize = lambda: adapter.authorize(snapshot)
    await authorize()
    for key, value in answers.items():
        field = fields[key]
        form = forms[field["form_index"]]
        base = {"organizationHostedJobsPageName": company, "formRenderIdentifier": form["id"],
                "formDefinitionIdentifier": form.get("sourceFormDefinitionId"), "path": key}
        if field["hosted_type"] == "File":
            if value != snapshot["resume_id"] or not adapter.load_resume:
                raise AppError("FORBIDDEN", "Only the reviewed, owned original resume may be uploaded.", 403)
            filename, original = await adapter.load_resume(value)
            if not original or len(original) > 5 * 1024 * 1024:
                raise AppError("INVALID_RESUME", "The stored resume exceeds the supported limit.", 413)
            handle = await upload(page, gate, authorize, company, filename, original)
            data = await rpc(page, gate, authorize, "ApiSetFormValueToFile", {**base, "fileHandle": handle})
            updated = data.get("setFormValueToFile")
        else:
            converted = await location_value(page, gate, authorize, field, value) if field["hosted_type"] == "Location" else scalar_value(field, value)
            data = await rpc(page, gate, authorize, "ApiSetFormValue", {**base, "value": converted})
            updated = data.get("setFormValue")
        entries = [e for s in (updated or {}).get("sections", []) for e in s.get("fieldEntries", []) if (e.get("field") or {}).get("path") == key]
        if not updated or updated.get("id") != form["id"] or len(entries) != 1:
            raise AppError("BROWSER_ACTION_FAILED", "The employer did not return the updated form field.", 409)
        received = entries[0].get("fieldValue") or {}
        verified = received.get("filename") == filename and bool(received.get("id")) if field["hosted_type"] == "File" else json_equal(received.get("value"), converted)
        if not verified:
            raise AppError("BROWSER_ACTION_FAILED", "The employer's stored value differs from your reviewed answer.", 409)
        expected[key] = {"id": received["id"], "filename": received["filename"]} if field["hosted_type"] == "File" else {"value": converted}
        current[field["form_index"]] = updated

    audit_forms(forms, current, expected)

    # Reload only the site's own previously observed reCAPTCHA script after approval.
    gate.update(hosted=True, approved=True, authorize=authorize, permit=None)
    await page.evaluate(r"""() => {
      for(const old of document.querySelectorAll('script[src]')) {
        const url=new URL(old.src);
        if(['www.google.com','www.recaptcha.net'].includes(url.hostname) && /^\/recaptcha\/(api|enterprise)\.js$/.test(url.pathname)) {
          const script=document.createElement('script');script.src=old.src;script.nonce=old.nonce;
          old.replaceWith(script);break;
        }
      }
    }""")
    permit = FinalPermit(url, forms, observed.get("notice_id"))
    receipt = asyncio.get_running_loop().create_future()

    async def receive(response):
        if response.request != permit.request or receipt.done():
            return
        try:
            result = await response.json()
            data = result.get("data", {}).get("submitMultipleFormsAction" if len(forms) > 1 else "submitApplicationFormAction", {})
            confirmations = [data.get("applicationFormResult")] + (data.get("surveyFormResults", []) if len(forms) > 1 else [])
            ok = (200 <= response.status < 300 and not result.get("errors") and len(confirmations) == len(forms)
                  and all(c and c.get("__typename") == "FormSubmitSuccess" for c in confirmations)
                  and not (data.get("messages") or {}).get("blockMessageForCandidateHtml"))
            receipt.set_result(ok)
        except (ValueError, TypeError, AttributeError):
            receipt.set_result(False)

    page.on("response", receive)
    await authorize()
    gate["permit"] = permit
    await page.locator("button.ashby-application-form-submit-button").click()
    try:
        verified = await asyncio.wait_for(receipt, 30)
    except TimeoutError:
        raise AppError("SUBMISSION_VERIFICATION_FAILED", "The employer did not confirm submission. CAPTCHA or another manual step may be required; check the employer before retrying.", 409) from None
    if not verified or not permit.consumed or permit.rejected:
        raise AppError("SUBMISSION_VERIFICATION_FAILED", "The employer rejected or did not confirm the application; automatic retry is disabled.", 409)
    return {"verified": True, "confirmation": "Employer returned FormSubmitSuccess for the approved application and surveys.",
            "form_schema_version": observed["version"], "adapter_version": TRANSPORT}
