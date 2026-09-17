# Turio — Application Automation

## 1. Initial target

The initial Browser Use trial is limited to:
- 1Password
- Linear
- Supabase
- Vercel
- Notion

A company is considered supported only after its actual application workflow is tested end-to-end and evidence is recorded.

## 2. Application adapter

```python
class ApplicationAdapter:
    def can_handle(self, url): ...
    def inspect_form(self, page): ...
    def normalize_field(self, raw_field): ...
    def fill_field(self, field, value): ...
    def upload_resume(self, field, file_ref): ...
    def validate(self, page): ...
```

The exact Python interface may evolve, but website-specific behavior must remain isolated behind the adapter boundary.

## 3. Canonical form schema

The database/API canonical names are:

```json
{
  "field_key": "",
  "label": "",
  "normalized_intent": "",
  "input_type": "",
  "required": true,
  "options": [],
  "source_locator": ""
}
```

The persistent database row id is still the field's `id`/`field_id` reference where required by API payloads.

## 4. Profile-to-form matching

Priority:

```text
exact canonical intent
→ normalized synonym
→ safe semantic match
→ manual/user resolution
```

The mapper must reuse stored information and must not ask the user again for data already present.

## 5. New information

When a required field cannot be safely populated:

```text
Detect missing field
→ ask user once
→ save answer after confirmation
→ reuse saved answer on later compatible applications
```

## 6. Resume upload

Use the original stored resume file reference. Do not regenerate the resume for an ordinary application submission.

## 7. Sensitive questions

For work authorization, sponsorship, disability, demographic information, or other sensitive data:
- use explicit stored answers only,
- otherwise ask the user,
- never infer from nationality, name, location, education, or resume language.

## 8. Final submission

The agent must stop before final submission until the user explicitly approves the reviewed application.

### Visible browser mode

`BROWSER_HEADLESS` defaults to `true`. Setting it to `false` passes headed mode
to the existing Browser Use runtime. This does not enable automation or alter
domain, resume-integrity, review or submission guards.

Headed mode needs a usable desktop display on the **backend host**. It does not
open the remote user's Chrome, and setting it false in a display-less Docker
container is not a streaming solution. Keep the default in the current Docker
stack. Configuration forwarding/cleanup has unit coverage; a real headed desktop
session and live employer compatibility are not yet verified.

## 9. Failure handling

Show and record:
- stage,
- site/platform,
- failure reason,
- diagnostic id,
- retry availability.

Use bounded retries only.

## 10. Unsupported flow

```text
Stop automation
→ explain unsupported workflow
→ preserve discovered data
→ offer manual continuation
→ track status
```

Never claim an application was submitted when it was not.

## 11. Native-form verification boundary

ADR-033 limits the next verification step to fully intercepted synthetic forms
using the actual browser runtime. Production destinations remain restricted.
Approval must cover the native form destination and values, including original
resume bytes; unrelated requests and duplicate mutation attempts cannot establish
success. JS-only/custom ATS transports remain unsupported until separately audited.
Local fixture evidence is not per-company live support evidence.

The implemented v2 native contract accepts explicit UTF-8 POST forms using
native multipart or URL-encoded bodies. Named hidden fields, multiple inputs and
custom widgets require a separate adapter. Missing optional answers are cleared,
not silently inherited from page defaults. The action/controls are rechecked
around authorization; actual text/file data is checked by a single-use request
permit. Stored resume bytes must also match the upload checksum.

Context page requests are sealed when candidate filling begins; only the approved
matching POST may pass. Service workers/page WebSockets are blocked. Teardown
closes the context/CDP connection, owned browser and driver.

Local result: 130 full-suite passes, including 17 actual-browser fixtures and 14
payload tests. See `evidence/phase6-local-verification-2026-09-15.md`. Arbitrary
JSON transports, pre-submit RPC/uploads, CSRF fields, redirects and live Ashby
pages have not been verified. Do not weaken the guard to make a live page pass.
