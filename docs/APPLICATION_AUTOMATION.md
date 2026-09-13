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
