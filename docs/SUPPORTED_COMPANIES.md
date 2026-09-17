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

As of September 15, 2026, **none of the five companies has a verified live run**.
The native adapter has local intercepted-fixture evidence only. Synthetic URLs
matching the allowlist were served entirely from fixtures and did not contact
employers; they must not be listed as company support evidence.

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

### September 16 discovery expansion (not support validation)

The checksum-verified September 15 Stapply Ashby company feed contains **3,448**
companies. The separately prepared operational inventory retains all five trials
and prioritizes Ashby companies with available jobs for future validation.
The merged job slices contain jobs for **2,917** company slugs (previous local
slice: 2,911). No new ATS adapter or browser allowlist entry was added.

The local `data/stapply-company-inventory.json` catalog explicitly marks every
entry `automation_supported: false`. Job-board/logo discovery is not application
flow validation. Actual source logos were observed for 0g Labs, 0x, 1Password,
Linear, Supabase and Notion; Vercel did not expose an image in this check and no
logo was guessed.

Reproduce the separate operational CSV using `scripts/prepare_company_inventory.py`
with the original/local job slice, downloaded current Ashby slice and company
feed. Supply `docs/evidence/company-logo-sources-2026-09-16.json` for the observed
logo metadata, then import the output using the existing ingestion service.
Source URLs/checksums: [[evidence/stapply-expansion-2026-09-16]].
Keep `data/ashby-jobs.csv` unchanged for the Phase 4 benchmark.

Add a new ATS only after:
- Ashby workflow is stable,
- field mapping is reusable,
- evaluation evidence exists.

Then evaluate one new ATS at a time.


## End-to-end evidence

A company becomes **supported** only after recording at minimum:
- tested job URL,
- application URL/workflow,
- form-schema version,
- test date,
- success/failure result,
- artifact or screenshot reference,
- known unsupported fields/edge cases.
