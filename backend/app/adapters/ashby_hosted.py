"""Hosted form inspection and approved filling. Submission stays with the user."""
import asyncio
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from app.adapters.ashby_queries import PUBLIC_QUERIES, PUBLIC_QUERY_VARIANTS
from app.core.errors import AppError
from app.ml.scoring import digest

VERSION = "ashby-hosted-v1"


def automatic_supported(form):
    return bool(form and form.get("version") == VERSION and form.get("submission_transport") == "ashby-hosted-v2"
                and form.get("schema_contract_version") == "stable-actions-v1"
                and form.get("manual_submission_required") is False)


def require_available(page):
    reason = getattr(page, "_turio_hosted_unavailable", None)
    if reason:
        raise AppError("JOB_UNAVAILABLE", reason, 404)


def bind_metadata(page, url):
    page._turio_metadata_ready = asyncio.Event()

    async def receive(response):
        if not public_read(response.request, url) or response.request.post_data_json["operationName"] != "ApiJobPosting":
            return
        try:
            payload = await response.json()
            if payload.get("errors") or "jobPosting" not in (payload.get("data") or {}):
                return
            posting = payload["data"]["jobPosting"]
            if posting is None:
                page._turio_hosted_unavailable = "The employer has removed this posting. It has been hidden from active jobs."
                return
            deadline = posting.get("applicationDeadline")
            if deadline:
                parsed = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
                if parsed.tzinfo is not None and parsed < datetime.now(timezone.utc):
                    page._turio_hosted_unavailable = "The employer's application deadline has passed. It has been hidden from active jobs."
                    return
            form = posting["applicationForm"]
            forms = [form, *(posting.get("surveyForms") or [])]
            page._turio_hosted_forms = forms
            form = {**form, "sections": list(form["sections"])}
            form["sections"] = [{**s, "_turio_form_index": index} for index, group in enumerate(forms) for s in group.get("sections") or []]
            form["_turio_form_controls"] = ([{"definition_id": f.get("sourceFormDefinitionId"), "controls": f.get("formControls", [])} for f in forms]
                                            if any(f.get("formControls") for f in forms) else [])
            form["_turio_notice_id"] = (posting.get("automatedProcessingLegalNotice") or {}).get("automatedProcessingLegalNoticeRuleId")
            page._turio_hosted_form = form
        except (ValueError, KeyError, TypeError, AttributeError):
            pass
        finally:
            page._turio_metadata_ready.set()
    page.on("response", receive)


def public_read(request, application_url):
    """Permit only pinned public queries with posting/company-only variables."""
    target, page = urlparse(request.url), urlparse(application_url)
    if request.method != "POST" or target.path != "/api/non-user-graphql" or target.hostname != page.hostname:
        return False
    try:
        body = request.post_data_json
        operation = body["operationName"]
        variables = body["variables"]
        company, posting = page.path.strip("/").split("/")[:2]
        queries = (PUBLIC_QUERIES.get(operation), *PUBLIC_QUERY_VARIANTS.get(operation, []))
        if set(body) != {"operationName", "variables", "query"} or not isinstance(body["query"], str) or body["query"] not in queries:
            return False
        if parse_qs(target.query) != {"op": [operation]}:
            return False
        if operation == "ApiJobPosting":
            return variables == {"organizationHostedJobsPageName": company, "jobPostingId": posting}
        return operation == "ApiOrganizationFromHostedJobsPageName" and variables in (
            {"organizationHostedJobsPageName": company},
            {"organizationHostedJobsPageName": company, "searchContext": "JobPosting"},
        )
    except (ValueError, KeyError, TypeError):
        return False


RADIO_OPTIONS = r"""els => {
  const options = els.map(e=>({value:e.value,label:[...(e.labels||[])].map(l=>l.textContent.trim()).join(' ') || e.value}));
  if (new Set(options.map(o=>o.value)).size !== options.length)
    return options.map(o=>({value:o.label,label:o.label}));
  return options;
}"""

INSPECT_HOSTED = r"""metadata => {
  const radioOptions = """ + RADIO_OPTIONS + r""";
  const visible = el => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  const fields = [];
  for (const section of metadata.sections || []) {
    if (section.isHidden) continue;
    for (const entry of section.fieldEntries || []) {
      if (entry.isHidden) continue;
      const field = entry.field, key = field.path;
      const source = '[data-field-path="' + CSS.escape(key) + '"]';
      const wrappers = [...document.querySelectorAll(source)].filter(visible);
      if (wrappers.length !== 1) return {error:'A hosted field is missing or ambiguous. Continue manually.'};
      const wrapper = wrappers[0], label = wrapper.querySelector('label');
      const controls = [...wrapper.querySelectorAll('input,select,textarea')];
      const control = controls.find(e => e.type === 'file' || visible(e));
      const title = [label?.textContent, field.title, field.humanReadablePath].map(v=>v?.trim()).find(Boolean) || '';
      if (!key || !title) return {error:'A hosted field has no stable identity or label.'};
      let kind = 'manual', type = field.type === 'LongText' ? 'textarea' : 'text', options = [];
      if (control && !field.isMany) {
        if (field.type === 'Boolean' && control.type === 'checkbox') {
          kind = 'boolean'; type = 'select';
          options = [{value:'true',label:'Yes'},{value:'false',label:'No'}];
        } else if (control.type === 'radio') {
          kind = 'radio'; type = 'select';
          options = radioOptions(controls.filter(e=>e.type==='radio'));
          if (new Set(options.map(o=>o.value)).size !== options.length)
            return {error:'A radio question has indistinguishable choices. Continue manually.'};
        } else if (control.tagName === 'SELECT') {
          kind = 'select'; type = 'select';
          options = [...control.options].filter(o=>o.value).map(o=>({value:o.value,label:o.text}));
        } else if (field.type === 'ValueSelect' && control.getAttribute('role') === 'combobox') {
          kind = 'manual'; type = 'select';
          options = (field.selectableValues || []).filter(o=>!o.isArchived).map(o=>({value:o.value,label:o.label}));
        } else if (field.type === 'MultiValueSelect' && field.selectableValues?.length > 1) {
          kind = 'manual'; type = 'multiselect';
          options = field.selectableValues.filter(o=>!o.isArchived).map(o=>({value:o.value,label:o.label}));
        } else if (control.getAttribute('role') !== 'combobox' && ['text','email','tel','url','number','checkbox','file','textarea'].includes(control.type)) {
          kind = 'plain'; type = control.type;
        }
      }
      const description = document.createElement('textarea');
      description.innerHTML = (entry.descriptionHtml || '').replace(/<[^>]*>/g,' ');
      const help = [description.value.trim(),control?.getAttribute('placeholder')?.trim()]
        .filter(v=>v && !/^(type here|enter text|your answer)[.\s…]*$/i.test(v));
      const supported = !field.isMany && ['String','LongText','Email','Phone','Url','Number','Boolean','ValueSelect','Location','File'].includes(field.type)
        || (!field.isMany && field.type === 'MultiValueSelect' && field.selectableValues?.length > 0);
      fields.push({field_key:key,name:key,label:title,input_type:type,required:!!entry.isRequired,
        source_locator:source,options,control_kind:kind,help_text:help.join(' ') || null,
        hosted_type:field.type,form_index:section._turio_form_index || 0,rpc_supported:!!supported,
        selectable_values:field.selectableValues || [],location_types:field.locationTypes || null});
    }
  }
  if (!fields.length || fields.length > 100 || new Set(fields.map(f=>f.field_key)).size !== fields.length)
    return {error:'Hosted fields must have bounded, unique identities.'};
  const keys = new Set(fields.map(f=>f.field_key));
  if ([...document.querySelectorAll('[data-field-path]')].some(el=>visible(el) && !keys.has(el.dataset.fieldPath)))
    return {error:'The page contains a field missing from its public form schema. Continue manually.'};
  const forms = metadata._turio_form_controls || [];
  const supported = forms.length > 0 && forms.every(f=>f.controls.length === 1 && f.controls[0].identifier && /^submit$/i.test(f.controls[0].title))
    && fields.every(f=>!f.required || f.rpc_supported);
  const stableForms = forms.map(f=>({definition_id:f.definition_id,controls:f.controls.map(c=>({title:c.title}))}));
  return {version:'ashby-hosted-v1',definition_id:metadata.sourceFormDefinitionId || null,fields,
    manual_submission_required:!supported,submission_transport:supported ? 'ashby-hosted-v2' : null,
    schema_contract_version:supported ? 'stable-actions-v1' : null,form_controls:stableForms,notice_id:metadata._turio_notice_id || null};
}"""


async def schema(page):
    if hasattr(page, "_turio_metadata_ready"):
        await asyncio.wait_for(page._turio_metadata_ready.wait(), 15)
    require_available(page)
    metadata = getattr(page, "_turio_hosted_form", None)
    if not metadata:
        raise AppError("UNSUPPORTED_APPLICATION", "The hosted application form could not be read. The posting may have expired.", 422)
    # Include optional survey questions; never silently omit a rendered section.
    result = await page.evaluate(INSPECT_HOSTED, metadata)
    if result.get("error"):
        raise AppError("UNSUPPORTED_APPLICATION", result["error"], 422)
    return result


async def fill(page, snapshot, resume):
    """Fill reviewed supported controls; return fields needing the user's browser interaction."""
    observed = await schema(page)
    if digest(observed) != digest(snapshot["schema"]):
        raise AppError("CONFLICT", "The employer form changed. Prepare and review again.", 409)
    keys = {f["field_key"] for f in observed["fields"]}
    if set(snapshot["answers"]) - keys:
        raise AppError("CONFLICT", "The review contains unknown fields.", 409)
    manual = []
    # Upload first, then write reviewed text values over any upload defaults.
    fields = sorted(observed["fields"], key=lambda f: f["input_type"] != "file")
    for field in fields:
        if not field["required"] and field["field_key"] not in snapshot["answers"]:
            continue
        value = snapshot["answers"].get(field["field_key"])
        wrapper = page.locator(field["source_locator"])
        kind = field["control_kind"]
        if kind == "boolean":
            if value not in {"true", "false"}:
                raise AppError("MISSING_REQUIRED_FIELD", "Confirm yes or no for this question.", 422)
            control = wrapper.locator('input[type="checkbox"]')
            await control.set_checked(value == "true")
            if await control.is_checked() != (value == "true"):
                raise AppError("BROWSER_ACTION_FAILED", "A filled value differs from your reviewed answer.", 409)
            continue
        if kind == "manual":
            manual.append(field["label"])
            continue
        if field["input_type"] == "file":
            if value:
                if value != snapshot["resume_id"] or resume is None:
                    raise AppError("FORBIDDEN", "Only the reviewed original resume can be uploaded.", 403)
                await wrapper.locator('input[type="file"]').set_input_files(resume)
            continue
        if kind == "radio":
            if value:
                radio = wrapper.locator('input[type="radio"]')
                options = await radio.evaluate_all(RADIO_OPTIONS)
                matches = [index for index, option in enumerate(options) if option["value"] == value]
                if options != field["options"] or len(matches) != 1:
                    raise AppError("CONFLICT", f"A reviewed option for {field['label']} is no longer available. Prepare and review again.", 409)
                await radio.nth(matches[0]).check()
                if not await radio.nth(matches[0]).is_checked():
                    raise AppError("BROWSER_ACTION_FAILED", "A filled choice differs from your reviewed answer.", 409)
            else:
                manual.append(field["label"])
            continue
        control = wrapper.locator("input,select,textarea").first
        if kind == "select":
            await control.select_option(value or "")
        elif field["input_type"] == "checkbox":
            await control.set_checked(bool(value))
        else:
            await control.fill(value or "")
        actual = await control.is_checked() if field["input_type"] == "checkbox" else await control.input_value()
        expected = bool(value) if field["input_type"] == "checkbox" else value or ""
        if actual != expected:
            raise AppError("BROWSER_ACTION_FAILED", "A filled value differs from your reviewed answer.", 409)
    return manual
