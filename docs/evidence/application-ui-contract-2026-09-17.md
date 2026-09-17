# Application frontend contract verification — September 17, 2026

## Result

Seven frontend interaction checks passed against the existing local frontend,
using only synthetic responses:

1. Stored profile values are read-only and the original resume selection is shown.
2. Missing required information prevents review and surfaces the API error.
3. Factual draft answers require explicit confirmation.
4. Submission controls require explicit approval.
5. Editing an answer hides submission controls and requires saving/reviewing
   again; the previous approval does not carry over.
6. The application page fits a 390px viewport without document overflow.
7. Retrying after a simulated response failure retains the idempotency key.

All **13 API requests were intercepted**. There were zero unexpected requests
and zero page errors. No real account, resume upload or backend mutation occurred;
no employer endpoint was contacted. The fixture uses an `.invalid` employer URL.

Script: `scripts/verify_application_ui_contract.py`.
Local output: `.runtime/application-ui-contract/result.json`,
`.runtime/application-ui-contract/application-mobile.png`,
`.runtime/application-ui-contract.log`.

The screenshot was captured by the script; separate visual image inspection was
unavailable in this tool environment. The layout result is a measured overflow
check, not a claim of manual visual review.

## Evidence boundary

This is a frontend-only contract test with simulated API responses. It does not
replace the real UI/proxy/API/storage integration smoke, the native browser
adapter tests, human relevance annotation or permitted live-company validation.
The quarantined synthetic benchmark was not opened, frozen or evaluated.

The isolated frontend-server launch was retried once in response to the user's
continuation and again denied by policy. No alternate route was used to launch
that server. Full integration remains unexecuted locally.

## CI preparation

Added an `application-ui` job to `.github/workflows/checks.yml`. It installs the
existing dependencies, builds the frontend, starts disposable loopback fixture
services, checks the test sentinel, runs `smoke_ui.py --application-fixture`,
cleans up its owned processes and retains logs/screenshots.

Python/YAML parsing, test-only environment settings and `bash -n` validation of
the CI shell step passed. `git diff --check` passed with existing line-ending
warnings. **No push or GitHub CI execution occurred.** Configuration is not a
passed integration run.

No production backend/frontend code changed; previous backend and build results
were not rerun merely to repeat unchanged checks.

## Changed files

- `scripts/verify_application_ui_contract.py`
- `.github/workflows/checks.yml`
- `docs/TESTING.md`
- This report and current-context/session/changelog/progress/TODO notes

## Remaining work

Run the complete guarded integration workflow once the isolated frontend launch
is permitted, or through an authorized CI execution. Human-data evaluation and
real-company acceptance gates remain unverified. The project is not yet marked
finished.
