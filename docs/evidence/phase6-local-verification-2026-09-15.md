# Phase 6 — local native-browser verification

Date: September 15, 2026.

## Result

**130 passed in 117.77s**, with no failures or skips and no warnings reported in
the final pytest run. This includes **17 actual-browser fixture cases**, **14
pure native-payload permit cases**, the existing backend tests and the real local
SBERT API/cache smoke.

- Retained test output: `phase6-local-2026-09-15.xml`.
- Machine-readable summary: `phase6-local-2026-09-15.json`.
- Runtime: Python 3.13.2, Browser Use 0.11.13, Playwright 1.62.0.
- Schema/adapter: `native-form-v2` / `ashby-native-v2`.
- The unchanged frontend production build passed.

## Isolation

These are not employer tests. The fixture uses synthetic URLs matching the
production destination policy, but every browser-page HTTP request terminates
in a Playwright fixture handler or is aborted. The handler never forwards to an
employer. Page WebSockets and service workers are blocked. Browser Use connects
only to its own local Chromium debugging endpoint. No existing user browser
profile is used.

The tests select the installed Playwright Chromium executable explicitly.
API tests use isolated SQLite and in-memory object storage, not PostgreSQL or
MinIO. Live-site certificates, ATS integrations, deployment/autodiscovery and
production concurrency are not established by this evidence.

## Verified behavior

- Real DOM inspection extracts stable labels without including dropdown options.
- Native POST action, method, encoding, field names and checkbox values are part
  of the review schema. A changed action or form stops the attempt.
- Missing answers do not silently inherit prefilled text or checked boxes.
- Filling and review make no submission POST.
- The stored original resume is checked against its upload checksum, placed in
  the real file input, read back by digest, and compared again in the outgoing body.
- Authorization is checked immediately before clicking, followed by another
  form/value check.
- A single-use permit allows only the expected action and reviewed native body.
  Altered text/files, extra or duplicated fields, ambiguous encodings/headers,
  unsupported JSON transport, unrelated requests and duplicate POSTs are rejected.
- Confirmation text alone or an unrelated successful request cannot establish
  success. A matching accepted POST and changed confirmation state are required.
- Both native form navigation and native FormData submission were exercised.
- CAPTCHA/custom controls stop instead of being bypassed or guessed.
- Field operations have at most two retries. Submission is never automatically retried.
- Owned browser/context/CDP resources are closed; the local debugging port is
  unreachable after the tested context exits.
- The actual application API performs upload → inspect/map → answer → review →
  explicit approval → browser submission against the fixture. Replaying the
  approval returns the stored response without a second browser or POST.

## Reproduced defects before fixes

1. Wrapped dropdown options contaminated the field label.
2. Unapproved prefilled text and checked optional boxes could be sent.
3. Changing the form action was not detected by the old review schema.
4. Unrelated successful POSTs plus confirmation text could produce false success.
5. Modified outgoing data and duplicate POSTs were not prevented.
6. Stored object bytes were not compared with the original upload checksum.

All have regression coverage. An intermediate browser run also exposed a Windows
pipe cleanup warning; teardown now explicitly closes the context and CDP
connection, kills the owned Browser Use session and stops the driver. The final
full run reported no warnings.

## Reproduction

Install the existing base requirements plus the pinned optional browser/ML
requirements. Install Chromium and download the pinned model using the existing
setup scripts. Then, from `backend/` on Windows:

```powershell
$env:TURIO_BROWSER_TESTS='1'
$env:TURIO_ML_SMOKE='1'
$env:HF_HUB_OFFLINE='1'
$env:ANONYMIZED_TELEMETRY='false'
./.venv/Scripts/python.exe -m pytest -q --tb=short -p no:cacheprovider --junitxml=../docs/evidence/phase6-local-2026-09-15.xml
```

Browser-only checks can select `tests/test_browser_adapter.py`,
`tests/test_native_submission.py`, and `tests/test_storage.py`.
A dedicated native-browser CI job was added but has not been run remotely.

## Still open

No company becomes supported from fixture evidence. Hidden/CSRF fields,
pre-submit upload/read RPCs, custom widgets, arbitrary JSON serializers and
redirect-based confirmation require separately audited handling. Browser
assistance remains disabled by default. Real PostgreSQL/MinIO/Compose checks,
durable workers and interruption reconciliation, live workflow evidence,
production hardening and final research remain outstanding.
