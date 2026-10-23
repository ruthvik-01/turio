# Resume, company discovery and browser-availability follow-up

## Reproduced and changed

- The generic resume block splitter treated every description bullet as a new
  project. Reproduced two projects becoming five entries, including bullet
  sentences used as project names. A project-specific splitter now keeps those
  bullets with their heading, preserves description line breaks, recognizes
  additional project/section headings, and extracts intact multiword skills or
  explicitly labelled technology lists without inferring technologies.
- Parser version is now `rules-v2`. Re-uploading the same PDF from an older parser
  re-extracts the profile and retains its original resume ID/object. A regression
  also exposed an unnecessary duplicate object write on parser upgrades; fixed.
  Existing profiles are not silently overwritten. Re-upload once and review to
  apply the new rules; no per-job upload is needed.
- Simplified the resume upload area to a labelled file input and Upload resume
  button using existing styling. Reset the selected file after success and keep
  PDF/size validation. Updated existing smoke-test button locators.
- Supabase was already present in the 3,448-company catalog: pre-change live
  search returned its actual name/slug and displayed the dropdown. The initial
  list only showed 20 companies without explaining that limit. Added a
  full-catalog search hint/count and Enter selection of an exact name/slug,
  without requiring an ArrowDown first. No catalog data or jobs were invented.
- Added owner-scoped `GET /applications/{id}/capability`, reusing adapter
  configuration/URL checks without browser operations or state changes.
  Application Preparation now explains unavailability before clicking and
  disables Apply with Agent when unavailable. Available means experimental
  preparation can be attempted, not live company validation.

## Verification

- Initial targeted run: 52 passed, one new regression caught duplicate storage
  writes on parser upgrades. After the fix, all 19 resume tests passed.
- Full backend/native-browser/model suite: **209 passed, 1 failed in 139.06s**.
  The unrelated auth-limit test straddled a fixed-window boundary: its first
  request completed at 12:24:00.165 UTC after 212.63 ms, so it began in the
  preceding minute. The test assumes all three attempts use the same window.
  Isolated unchanged test rerun: **1 passed in 0.70s**. No auth/rate-limit code
  or test was changed; do not report the full run as an all-green run.
- Frontend production build and typecheck passed. Docker backend, worker and
  frontend builds succeeded and were deployed without resetting data volumes.
- Existing-frontend application contract: **7 checks passed**, 14 intercepted
  API requests, no unexpected requests/page errors. Explicit approval, fresh
  review after changes and same-key retry safeguards remain covered. This is
  still not the previously blocked full fixture-approval integration run.
- Live local UI regression: **6 check groups passed**, using a synthetic
  account/PDF, the real local PostgreSQL/storage/API/proxy/frontend, and no
  employer requests:
  - Upload, extraction into one project, saved profile after reload.
  - 390px profile layout without horizontal overflow (DOM check).
  - Supabase suggestions/Enter selection returning **61 actual jobs**.
  - Distinct company-filtered pages with stable totals.
  - Search + company + location + platform, resetting pagination.
  - Stored resume reused by application preparation; disabled assistance
    explained before clicking; application remains created/unsubmitted.
- The new browser test initially used overly strict accessible-label locators
  for textarea/select controls. Corrected the test locators, not application
  data. The final run passed with no page errors/unexpected requests.
- Mobile screenshot saved locally but not visually reviewed: the available image
  inspection tool rejected image input. No visual-review claim.

## Main changed files

- Backend: `app/services/resume_parser.py`, `resume_pipeline.py`,
  `app/api/v1/applications.py`, `app/schemas/application.py`;
  `tests/test_resume_projects.py`, `tests/test_applications.py`.
- Frontend: `components/profile.tsx`, `company-filter.tsx`,
  `applications.tsx`, `app/globals.css`.
- Verification scripts: `verify_profile_company_ui.py`,
  `verify_application_ui_contract.py`, `smoke_ui.py`,
  `verify_opportunity_ui.py`.
- API/automation docs and project handoff notes.

## Limits

The user's actual PDF was not supplied; the reproduced bullet-grouping bug and
tested layouts are fixed, not every possible PDF layout. No live automation was
enabled and no company was marked supported. Human Phase 4 evidence remains
absent and the quarantined synthetic benchmark was not frozen/evaluated.
These follow-up changes are deployed locally, not yet committed/pushed.

Raw local logs/results: `.runtime/usability-*.log`,
`.runtime/profile-company-ui/result.json`,
`.runtime/usability-application-contract/result.json`.
