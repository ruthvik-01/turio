# Turio — Initial Supported Companies

## Initial trial set

| Company | Platform |
|---|---|
| 1Password | Ashby |
| Linear | Ashby |
| Supabase | Ashby |
| Vercel | Ashby |
| Notion | Ashby |

## Support status

A company is **supported** only after the actual selected job application workflow has been tested.

Using an ATS name alone is not sufficient.

## Test protocol

For each company:

```text
Open live job
→ Open application
→ Inspect form
→ Record fields
→ Map profile
→ Upload resume
→ Fill
→ Validate
→ User review
→ User-approved submit
→ Verify
→ Record result
```

## Per-company evidence

Store:

```text
company
job_url
application_url
platform
form_schema_version
browser_agent_version
test_date
success/failure
failure_reason
screenshot/artifact reference
```

## Expansion rule

Add a new ATS only after:
- Ashby workflow is stable,
- field mapping is reusable,
- evaluation evidence exists.

Then evaluate one new ATS at a time.
