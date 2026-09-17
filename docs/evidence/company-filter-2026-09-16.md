# Jobs Company autocomplete — September 16, 2026

## Fix

Company is now a searchable catalog-backed combobox in its existing filter slot.
It searches all 3,448 entries in the existing discovery catalog, not job-page
contents or ATS metadata. Matching canonical company names and slugs appear in a
bounded dropdown; choosing an option submits the canonical company name through
the existing exact-name job filter and resets pagination. Search, Location and
Platform remain separate and compose through the unchanged jobs repository query.
Companies with no jobs remain discoverable and yield an honest empty job result.

Typing is debounced; superseded responses cannot replace newer suggestions.
Keyboard arrows/Enter/Escape, mouse selection, loading/empty/error states and
mobile layout are covered. Unselected non-empty text prompts selection or clearing
rather than silently submitting an arbitrary company. No names are generated.
A real catalog employer named Ashby remains discoverable: company name/slug
matching does not mean matching every company's Ashby ATS metadata.

## API and source

Authenticated `GET /api/v1/jobs/companies?q=<name-or-slug>&limit=20` returns the
existing envelope with `{companies: [{company, slug}], total}`. Limit is 1–50;
query length is capped at 255. No Platform/current-page filter limits discovery.
The catalog is `stapply-company-inventory.json` beside the configured job dataset.
Reads are cached by path/file modification time/size and run off the async request
loop. A missing/unreadable catalog produces `COMPANY_CATALOG_UNAVAILABLE` (503),
not invented entries or an incomplete job-page fallback. No schema migration,
inventory re-import, architecture replacement or ATS-support expansion was needed.

## Verification

- Focused company/jobs/eligibility tests: **34 passed in 7.85s**.
- Full backend suite with native-browser and offline-model flags: **182 passed,
  one known failure in 125.98s**. The existing artificial 0.4-second heartbeat test
  returns interrupted instead of succeeded; it was not changed in this task.
- Frontend typecheck and production build passed. Backend/frontend Compose images
  were rebuilt and deployed to the existing local verification stack.
- Real catalog/API/PostgreSQL browser checks: **eight groups passed**, zero page
  errors. Covered all 3,448 catalog entries independently of current-page jobs,
  keyboard selection of Linear, disjoint paginated company results with stable
  totals, all four filters combined, clearing Company while retaining Platform,
  mouse selection of no-job Vercel, honest unknown-name results, Escape dismissal
  and 390px layout. Evidence: [[company-filter-2026-09-16/results]].
- Existing opportunity/resume UI regression: **eight groups passed**, no page
  errors or employer submissions, using the updated autocomplete selection.
- Whitespace check passed. Phase 4 and all explicit submission safeguards remain;
  Phase 5 was not started.

Browser test assertions were corrected to recognize Ashby as an actual employer
and to distinguish autocomplete options from native Platform select options.
Neither required changing product data or filtering out genuine catalog entries.

## Implementation/test files changed

- `D:/College/4-2 project/backend/app/api/v1/jobs.py`
- `D:/College/4-2 project/backend/app/schemas/job.py`
- `D:/College/4-2 project/backend/app/services/jobs.py`
- `D:/College/4-2 project/backend/app/repositories/company_catalog.py`
- `D:/College/4-2 project/frontend/components/jobs.tsx`
- `D:/College/4-2 project/frontend/components/company-filter.tsx`
- `D:/College/4-2 project/frontend/app/globals.css`
- `D:/College/4-2 project/backend/tests/test_company_filter.py`
- `D:/College/4-2 project/scripts/verify_company_filter.py`
- `D:/College/4-2 project/scripts/verify_opportunity_ui.py`

API/progress/context/session/changelog/decision documentation and the requested
local memory index were updated. Obsidian synchronization is not claimed.
