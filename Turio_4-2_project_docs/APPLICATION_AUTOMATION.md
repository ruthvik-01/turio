# Turio — Application Automation

## 1. Initial target

First implementation targets only supported Ashby workflows for:

- 1Password
- Linear
- Supabase
- Vercel
- Notion

## 2. Application adapter concept

```python
class ApplicationAdapter:
    def can_handle(self, url) -> bool: ...
    def inspect_form(self, page): ...
    def normalize_field(self, raw_field): ...
    def fill_field(self, field, value): ...
    def upload_resume(self, field, file_ref): ...
    def validate(self, page): ...
```

The exact interface can evolve; the architectural requirement is isolation.

## 3. Form schema

Normalize detected controls to:

```json
{
  "field_id": "",
  "label": "",
  "intent": "",
  "input_type": "",
  "required": true,
  "options": [],
  "locator_hint": ""
}
```

## 4. Profile-to-form matching

Priority:

```text
exact canonical intent
→ normalized synonym
→ safe semantic match
→ manual/user resolution
```

Never rely on an LLM alone when deterministic mappings are possible.

## 5. Resume upload

When a supported form requests a resume:

```text
stored resume file reference
→ browser upload control
→ original user file
```

Do not regenerate or edit the resume unless a separate user-approved feature explicitly requires it.

## 6. Sensitive questions

For work authorization, sponsorship, disability, demographic information, or other sensitive questions:

- use explicit stored user answers only,
- otherwise ask the user,
- never infer from nationality, name, location, education, or resume language.

## 7. Final submission

The final screen must clearly state:

> Review completed application before submission.

The system stops until the user explicitly confirms.

## 8. Automation failure handling

Show:

- what stage failed,
- target site,
- user-action request if needed,
- retry option,
- diagnostic id.

Store the failure in `application_events`.

## 9. Unsupported flow

When a site is unsupported:

```text
Stop automation
→ tell user the application cannot be completed automatically
→ preserve discovered data
→ optionally offer manual continuation
→ track status
```

Never pretend the application was submitted.
