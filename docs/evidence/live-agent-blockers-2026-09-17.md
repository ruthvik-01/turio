# Live Browser Use integration audit — September 17, 2026

## Scope and observations

Read-only browser inspection of the existing Supabase trial posting:
Product Manager - Marketplace, posting ID
`23c9ce7e-6b7b-4316-8f00-8f318e902441`.
Opened its Application tab. No candidate details were entered, no resume was
uploaded, and the submit control was not clicked.

The rendered application has no native HTML form. It contains labelled name,
email, resume, passport country, residence, social-profile and narrative controls,
a JavaScript Submit Application button, and reCAPTCHA elements.
Public page loading uses POST GraphQL reads named `ApiJobPosting` and
`ApiOrganizationFromHostedJobsPageName` at the same-origin non-user GraphQL
endpoint. These are observations, not permission to allow arbitrary POSTs.

## Current implementation mismatch

`backend/app/adapters/ashby.py` imports Browser Use's `Browser`, not its `Agent`.
It implements deterministic native-form operations through Playwright.
Its gate rejects all pre-approval POSTs, and its schema requires a unique native
form and native submission transport. The observed hosted page cannot satisfy
that contract even if browser automation is enabled.

The installed Browser Use Agent accepts an LLM and otherwise selects a
configured/default model. Turio's checked project environment/configuration
does not configure that integration. No unrelated process credential was used.
The existing project decision to avoid sending profile/resume data to an LLM
has not been silently reversed.

## Next decision and safeguards

User wants the actual agent operational. Resolve the intended model/provider
and candidate-data processing choice before implementing the LLM-driven path.
Website-specific JavaScript transport requires separate audited handling, not
relaxing the existing native POST permit.

Keep original-file integrity, owner isolation, bounded runtime, explicit review
and approval, and no fabricated submission outcomes. CAPTCHA challenges remain
human-handled; do not bypass them. A hosted browser needs an appropriate display
or viewing mechanism; Docker headless=false alone does not open the user's Chrome.

No automation flag or company support status changed. No production source change,
employer application, external LLM request, or effectiveness evaluation occurred
during this audit. Prior verification results are unchanged.
