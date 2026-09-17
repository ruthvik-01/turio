# Phase 5 functional verification — September 17, 2026

## Authorization and limits

The user authorized starting Phase 5 using synthetic data only for verification.
ADR-038 records the bounded exception to phase ordering. Phase 4 is still
unverified at its human-data boundary. The quarantined synthetic candidate
benchmark was not read by these tests, frozen or evaluated.

This run used existing isolated test profiles, PDFs, job rows and form adapters.
It does not establish matching effectiveness, consented human ground truth,
live-employer compatibility or automation support.

## Inspection and change

Inspected the existing application state/service/repository and canonical field
mapping, API contract, approval UI and resume-preparation tests. Retained the
architecture and frontend design. No production-code defect was reproduced;
no production code, browser configuration or deployment setting was changed.

Added `test_phase5_reuses_one_resume_and_reviewed_profile_across_jobs` to
`backend/tests/test_applications.py`. It verifies:

- Actual synthetic PDF upload/processing and matching checksum.
- One stored upload reused by two distinct job applications.
- Application jobs equal the job objects returned by the matching API.
- Reviewed name/location override the values originally extracted from the PDF.
- Only the unanswered authorization question is initially missing.
- Explicitly confirmed authorization is reused only after save-for-reuse.
- Re-preparation retains answers and original selected resume.
- Both applications reach review with the original resume reference.
- Original bytes remain unchanged in isolated storage, with one storage write.
- No submission call, timestamp or submission-start event occurs.

The fake adapter verifies the review snapshot/reference, not a live file upload.
Separate real-browser fixtures below cover preparation/file selection without
posting.

## Actual verification

| Check | Result |
| --- | --- |
| Applications, recovery, job presentation, resume, matching and benchmark safeguards | 59 passed in 31.52s |
| Native browser preparation/safety fixtures | 5 passed in 22.26s |
| Frontend typecheck | Passed |
| Frontend production build | Passed |
| Diff whitespace check | Passed; existing line-ending warnings only |

Native browser cases: inspection labels/destination, original-file loading during
review fill without POST, pre-approval write/WebSocket blocking, and two bounded
fill-retry cases. Browser requests terminate in local intercepted fixtures.
These do not validate a real company application flow.

The API test selection also exercises simulated approval/idempotency with a
fake adapter; no request is submitted to an employer. No full-suite result is
claimed for this run.

Local logs:

- `.runtime/phase5-functional-tests-2026-09-17.log`
- `.runtime/phase5-browser-preparation-2026-09-17.log`
- `.runtime/phase5-frontend-2026-09-17.log`

## Phase status

Phase 5 functional verification has started and this bounded pass succeeded.
Stored-profile reuse, missing-field collection, explicit-sensitive-answer
handling, draft confirmation and repository compatibility have fixture evidence.
This is not exhaustive verification of every state transition or a new
end-to-end frontend browser test, and it does not mark Phase 5 fully VERIFIED.

Explicit final submission approval remains mandatory. Production browser
assistance remains disabled by default; no supported-company claims change.
Do not start live submissions or expand the adapter's transport policy on the
basis of these results.

## Files changed in this continuation

- `backend/tests/test_applications.py` — one end-to-end preparation regression.
- `docs/ADR.md`, `docs/PHASE_PLAN.md` — scoped user-authorized ordering exception.
- This report and context/progress/session/changelog/TODO/decision indexes.

No frontend or production backend code changes; no deployment was required.
