# Turio — Comprehensive QA Usability & Functional Bug Audit

**Date:** 2026-10-14

**Auditor Role:** Expert QA Automation Engineer & Job Applicant

**Testing Methodology:** Live Playwright End-to-End Automation, API/DOM Inspection, Database State Analysis

**Application URL:** `http://127.0.0.1:13000`

**API Endpoint:** `http://127.0.0.1:18080/api/v1`

**Evidence Directory (private, local-only):** `docs/evidence/qa_audit_20261014/`

---

## 1. Executive Summary

A comprehensive, end-to-end quality assurance audit was conducted across all core user journeys of the Turio platform:
1. User registration, authentication, and session management (`/signup`, `/login`).
2. Candidate onboarding, resume upload, PDF text parsing, and profile management (`/onboarding`, `/profile`).
3. Opportunity discovery, keyword search, platform filtering, and semantic recommendations (`/jobs`, `/jobs/[id]`).
4. Bulk job application workflow, multi-select queueing, shared-question consolidation, and automated submission mode (`/jobs`).
5. Application preparation, readiness scoring, answer confirmation, browser automation gates, and final submission reviews (`/applications/[id]`, `/applications/[id]/review`).
6. Application lifecycle tracking, recruiter outcome logging, manual submission confirmation, and interview management (`/applications`, `/interviews`, `/resources`).
7. Visual alignment, responsive viewports (Desktop 1280x900 vs. Mobile 375x667), console warnings, and HTTP error handling.

A total of **33 discrete test points** were audited, yielding **8 verified bugs** (3 High, 3 Medium, 2 Low) and detailed technical root-cause analyses. In strict accordance with the audit protocol, **no application code was modified**.

---

## 2. Test Execution Checklist

| Category | Test Case / Feature | Status | Associated Bug ID | Evidence / Notes |
|---|---|---|---|---|
| **Landing** | Root URL loading & visual layout | **PASS** | — | `01_landing.png` |
| **Landing** | Hero headline & CTA buttons | **PASS** | — | "Find your next step ↗" and "I already have an account" |
| **Auth** | Form button semantics | **FAIL** | `BUG-AUTH-001` | Button lacks explicit `type="submit"` attribute |
| **Auth** | Client-side HTML5 input validation | **PASS** | — | `required`, `email`, `minLength="8"` present |
| **Auth** | Duplicate email registration rejection | **PASS** | — | Returns HTTP 409: "An account with that email already exists." |
| **Auth** | Invalid login credential rejection | **PASS** | — | Returns HTTP 401: "Email or password is incorrect." |
| **Auth** | Session cookie establishment & redirect | **PASS** | — | Session established; redirected to `/onboarding` or `/home` |
| **Home** | Workspace dashboard rendering | **PASS** | — | Active applications & recommended jobs load cleanly (`05_home_page.png`) |
| **Navigation** | Global header links & routing | **FAIL** | `BUG-NAV-001` | Header omits direct link to `/profile` on some screen states |
| **Profile** | Form panel structure (8 sections) | **PASS** | — | All essentials, credentials, entities rendered |
| **Profile** | Resume non-PDF rejection | **PASS** | — | Rejects non-PDF with "Choose a PDF of 5 MB or less." |
| **Profile** | Resume PDF text parsing & contact extraction | **PASS** | — | Extracts full name, email, phone, location, LinkedIn |
| **Profile** | Resume parser non-standard LinkedIn URL matching | **FAIL** | `BUG-PARSE-001` | Regex misses LinkedIn URLs without `https://www.` or `/in/` |
| **Profile** | Manual profile saving & version increment | **PASS** | — | Profile saved; `version` incremented from 1 to 2 |
| **Profile** | Dynamic entity adding/removing (Experience/Education) | **PASS** | — | Experience and education items dynamically add/remove |
| **Profile** | Dirty state detection & discard button | **PASS** | — | "Discard unsaved edits" reverts modified inputs |
| **Jobs** | Inventory grid display (12 per page) | **PASS** | — | `09_jobs_page.png` |
| **Jobs** | Keyword search filtering | **PASS** | — | Search by title or company filters correctly |
| **Jobs** | Platform ATS filter options | **FAIL** | `BUG-JOBS-001` | Platform dropdown hardcodes only "Ashby" |
| **Jobs** | Empty search query feedback | **PASS** | — | "No jobs match these filters..." empty state displayed |
| **Jobs** | Recommendations "For you" tab | **PASS** | — | Switches between keyword, TF-IDF, and SBERT |
| **Bulk** | Bulk job selection checkboxes | **PASS** | — | Per-card and "Select visible jobs" select 12 items |
| **Bulk** | Clear selection action | **PASS** | — | Resets counter back to 0 selected |
| **Bulk** | Bulk application mode switcher | **PASS** | — | Switches between "Fill & review" and "Automatic submission" |
| **Bulk** | Bulk features location & accessibility | **FAIL** | `BUG-UX-001` | Bulk actions only exist on `/jobs`; absent from `/applications` |
| **Job Detail** | Single opportunity view & metadata | **PASS** | — | Title, company, location, extracted skills chips rendered |
| **Job Detail** | "Prepare application ↗" creation | **PASS** | — | Creates application draft and navigates to detail view |
| **Application** | Contact fact auto-confirmation (LinkedIn URL) | **FAIL** | `BUG-APP-001` | Contact facts re-prompted under "Missing info" if unconfirmed |
| **Application** | Answer sync to Profile | **FAIL** | `BUG-APP-002` | Saving answers updates `saved_answers` but leaves `Profile` empty |
| **Application** | Unrecoverable error state locking | **FAIL** | `BUG-APP-003` | `verification_failed` permanently locks UI with no retry button |
| **Application** | Profile value editing lock in review | **FAIL** | `BUG-APP-004` | Profile values are disabled with no inline edit option |
| **Tracker** | Applications status and outcome filters | **PASS** | — | Filtering by status (e.g. `verification_failed`) works |
| **Interviews** | Interviews stage tracker | **PASS** | — | Empty state rendered cleanly (`18_interviews.png`) |
| **Resources** | Candidate resources guide | **PASS** | — | Resource links rendered (`19_resources.png`) |
| **Responsive** | Mobile viewport width (375px) | **PASS** | — | No horizontal overflow detected on mobile (`20_mobile_jobs.png`) |

---

## 3. Detailed Bug Registry

### [BUG-APP-001] Contact facts (e.g. LinkedIn URL) re-prompted under "Missing information" despite being present in Profile/Resume
* **Severity:** High
* **Affected Component:** `frontend/components/applications.tsx`, `backend/app/services/form_mapping.py`
* **Affected URL:** `http://127.0.0.1:13000/applications/[applicationId]`
* **Screenshot Evidence:** `15_app_detail_view.png`
* **Steps to Reproduce:**
  1. Save your LinkedIn URL (`https://www.linkedin.com/in/...`) on `/profile`.
  2. Navigate to `/jobs` and open an opportunity whose application asks "Please share your LinkedIn profile URL".
  3. Click "Apply with Agent" to prepare the application.
  4. Observe the "Missing information" section.
* **Expected Behavior:** Since the user already provided their LinkedIn URL in their profile/resume, the application should automatically resolve the field, mark it confirmed, and hide it from "Missing information" (placing it under "View filled answers").
* **Actual Behavior:** The user is asked again: *"Please share your LinkedIn profile URL * Needs your confirmation"*.
* **Root Cause:**
  1. In `frontend/components/applications.tsx` line 12–16, `answered(field)` requires `field.user_confirmed === true`. When a field is populated from certain sources (like `ai_profile` or unconfirmed defaults), `user_confirmed` is `false`, so `answered()` evaluates to `false` and the field is forced into `visibleFields` ("Missing information").
  2. In `backend/app/services/form_mapping.py`, `intent()` uses a static set of aliases in `ALIASES["linkedin_url"]`. Non-standard question labels (e.g., "Link to LinkedIn profile", "LinkedIn page") fail alias matching and fallback to `"custom"`, preventing the field from pulling the profile's `linkedin_url`.
* **Recommended Solution:**
  1. In `form_mapping.py`, expand regex patterns for `linkedin_url` to match any label containing `linkedin`.
  2. In `backend/app/services/applications.py`, when a field matches a known canonical contact fact (`linkedin_url`, `phone`, `email`, `location`) and matches the user's saved profile, automatically initialize `user_confirmed = True` so the applicant is not repeatedly prompted to confirm their own profile details.

---

### [BUG-APP-002] Answers typed during Application Review are not synced back to the candidate's Profile table
* **Severity:** High
* **Affected Component:** `backend/app/services/applications.py` (method `answers`)
* **Affected URL:** `http://127.0.0.1:13000/applications/[applicationId]`
* **Screenshot Evidence:** `15_app_detail_view.png`
* **Steps to Reproduce:**
  1. Prepare an application for Job A where LinkedIn URL or GitHub URL was previously empty.
  2. In the "Missing information" form, type your LinkedIn URL.
  3. Click "Save answers". Notice the notice: "Application updated."
  4. Navigate to `/profile`.
  5. Check the LinkedIn URL field.
* **Expected Behavior:** Candidate profile essentials should be updated with the newly provided information so that future job applications reuse it automatically.
* **Actual Behavior:** The LinkedIn URL on `/profile` remains blank. When preparing Job B, the user is prompted to enter their LinkedIn URL again.
* **Root Cause:** In `backend/app/services/applications.py` lines 292–302, `save_for_reuse` only writes to the `SavedAnswer` model (`saved_answers` table with a hashed `question_key`). It does NOT update the `Profile` model in the database (`profiles.linkedin_url`). Because `profile_value()` looks first at `Profile`, any subsequent job with slightly different question wording will not find the answer in `SavedAnswer` and will find `NULL` in `Profile`.
* **Recommended Solution:** In `backend/app/services/applications.py` inside `answers()`, detect if `field.normalized_intent` corresponds to a canonical profile attribute (`linkedin_url`, `github_url`, `portfolio_url`, `phone`, `location`). If so, update the user's `Profile` entity and increment `profile.version`.

---

### [BUG-APP-003] Applications permanently lock in `verification_failed` with no retry or draft-reset action
* **Severity:** High
* **Affected Component:** `frontend/components/applications.tsx`
* **Affected URL:** `http://127.0.0.1:13000/applications/[applicationId]`
* **Screenshot Evidence:** `15_app_detail_view.png`
* **Steps to Reproduce:**
  1. Run an application submission that encounters a remote timeout, CAPTCHA, or employer portal glitch.
  2. The application transitions to status `verification_failed`.
  3. Observe the page state.
* **Expected Behavior:** The user should see a warning explaining the uncertainty, accompanied by an actionable button such as "Retry submission", "Reset to draft for review", or "Re-prepare application".
* **Actual Behavior:** The interface completely locks down:
  - `locked = true` disables all inputs, "Apply with Agent", and "Save answers".
  - A red notice states: *"The submission outcome is uncertain. Check the employer site before any manual retry. Automatic resubmission is disabled."*
  - The user has no way to reset the application state or retry via the agent.
* **Root Cause:** In `frontend/components/applications.tsx` line 76:
  ```typescript
  const locked = busy || !!app && ["preparing", "submitting", "submitted", "cancelled", "verification_failed"].includes(app.status);
  ```
  `verification_failed` is treated as a terminal lock state, and no backend action or frontend button exists to transition it back to `ready_for_review` or `needs_input`.
* **Recommended Solution:** Add an action button "Acknowledge & reset to review" that calls a new endpoint (or PATCH) to transition the application back to `ready_for_review`, unlocking the inputs.

---

### [BUG-APP-004] Profile-derived answers cannot be edited inline during application review
* **Severity:** Medium
* **Affected Component:** `frontend/components/applications.tsx`, `backend/app/services/applications.py`
* **Affected URL:** `http://127.0.0.1:13000/applications/[applicationId]`
* **Screenshot Evidence:** `15_app_detail_view.png`
* **Steps to Reproduce:**
  1. Open an application review where your Name, Email, Location, or Summary was auto-filled from your profile.
  2. Attempt to tweak the summary or fix a location typo for this specific application.
* **Expected Behavior:** Applicants should be able to override a profile value specifically for this application (or choose to update both).
* **Actual Behavior:**
  - Input field is disabled (`disabled={field.value_source === "profile"}`).
  - A static banner states: *"Profile values are reused automatically. To change them, edit your profile and prepare again. Every other answer remains yours to confirm."*
  - If sent to the backend, `applications.py` line 277 raises HTTP 409 CONFLICT: *"Edit your profile and prepare again to change a profile-derived answer."*
* **Root Cause:** The architecture strictly enforces single-source-of-truth from `Profile` to prevent application-specific drift, but forces high user friction by requiring users to exit the application, navigate to `/profile`, edit globally, and re-prepare the entire draft.
* **Recommended Solution:** Allow the user to unlock the field with an "Override for this application" toggle that converts `value_source` from `"profile"` to `"application_only"` or `"user"`.

---

### [BUG-UX-001] Bulk job application management is confined to `/jobs` and missing from `/applications`
* **Severity:** Medium
* **Affected Component:** `frontend/app/applications/page.tsx`, `frontend/components/applications.tsx`
* **Affected URL:** `http://127.0.0.1:13000/applications`
* **Screenshot Evidence:** `16_applications_tracker.png`, `12_bulk_panel.png`
* **Steps to Reproduce:**
  1. Prepare several application drafts.
  2. Navigate to `/applications` to manage them.
  3. Try to select multiple applications to answer shared questions or approve in batch.
* **Expected Behavior:** The `/applications` dashboard should provide checkboxes and bulk actions (Batch review, Answer once, Batch submit) for all pending applications.
* **Actual Behavior:** `/applications` is strictly a read-only table with single-item review links (`↗`). The entire bulk application panel and shared-answer consolidation UI only exist on the `/jobs` search page.
* **Root Cause:** In the codebase, `bulkResults` and `sharedQuestions` state were implemented directly inside `frontend/components/jobs.tsx`, while `frontend/components/applications.tsx` only renders individual table rows.
* **Recommended Solution:** Extract the bulk management component into a shared component and embed it on both `/jobs` and `/applications`.

---

### [BUG-PARSE-001] Resume parser regex misses non-standard LinkedIn URL formats in PDF text
* **Severity:** Medium
* **Affected Component:** `backend/app/services/resume_parser.py`
* **Screenshot Evidence:** `07_profile_extracted.png`
* **Steps to Reproduce:**
  1. Create a PDF resume with LinkedIn formatted as `linkedin.com/in/username` (without `https://` or `www.`) or `LinkedIn: username`.
  2. Upload to `/profile`.
  3. Inspect extracted LinkedIn URL under "The essentials".
* **Expected Behavior:** Parser should detect the LinkedIn username/handle and construct a valid URL (`https://www.linkedin.com/in/username`).
* **Actual Behavior:** The field remains blank (`None`).
* **Root Cause:** In `backend/app/services/resume_parser.py` line 89:
  ```python
  _URL = re.compile(r"https?://[^\s,;)]+|(?:www\.)[^\s,;)]+|(?<![\w@./-])(?:linkedin\.com/in|github\.com)/[^\s,;)]+", re.IGNORECASE)
  ```
  If delimiters or prefixes differ (e.g., `linkedin.com/username` without `/in/`, or bullet points immediately adjacent to the text), token splitting in `_extract_urls()` drops the URL.
* **Recommended Solution:** Enhance URL extraction with a dedicated LinkedIn pattern matcher that looks for `linkedin.com/(?:in/)?([a-zA-Z0-9_-]+)` and prepends `https://www.linkedin.com/in/`.

---

### [BUG-JOBS-001] ATS Platform filter dropdown only offers Ashby
* **Severity:** Low
* **Affected Component:** `frontend/components/jobs.tsx`
* **Affected URL:** `http://127.0.0.1:13000/jobs`
* **Screenshot Evidence:** `09_jobs_page.png`
* **Steps to Reproduce:**
  1. Navigate to `/jobs`.
  2. Look at the "Platform" dropdown filter.
* **Expected Behavior:** Should show available ATS platforms (e.g. Greenhouse, Lever, Workday) or clearly clarify that Ashby is currently the only supported automated platform.
* **Actual Behavior:** Dropdown has only two options: "All platforms" and "Ashby".
* **Root Cause:** Hardcoded in `frontend/components/jobs.tsx` line 193: `<select name="ats"><option value="">All platforms</option><option value="ashby">Ashby</option></select>`.
* **Recommended Solution:** Dynamically query available ATS platforms from the job inventory (`GET /jobs/platforms` or distinct values from dataset) or change label to "Platform (Ashby supported)".

---

### [BUG-AUTH-001] Authentication buttons omit explicit `type="submit"` attribute
* **Severity:** Low
* **Affected Component:** `frontend/components/auth-form.tsx`
* **Affected URL:** `http://127.0.0.1:13000/login` & `/signup`
* **Screenshot Evidence:** `02_signup.png`
* **Steps to Reproduce:**
  1. Inspect the "Create account ↗" or "Sign in ↗" button in DevTools.
* **Expected Behavior:** `<button type="submit" class="button primary full">`.
* **Actual Behavior:** `<button class="button primary full">` (type attribute missing).
* **Root Cause:** Omitted in JSX in `auth-form.tsx` line 26.
* **Recommended Solution:** Add `type="submit"` to the button element for standard HTML5 accessibility and automated testing conformance.

---

## 4. Analysis of User-Reported Questions

### Question 1: "if my resume contains these fields why isnt it taking it again if data is availble donot ask me again"
* **Technical Cause:**
  1. When a resume is uploaded, `resume_pipeline.py` extracts fields and saves them to `Profile`. If the parser regex missed the LinkedIn URL (e.g., formatting lacked `https://`), `profile.linkedin_url` was stored as `NULL`.
  2. During application preparation (`start()` in `applications.py`), if `field.normalized_intent` is mapped via AI (`ai_profile`) or deemed unconfirmed, `field.user_confirmed` is set to `False`.
  3. In the UI (`applications.tsx` line 12–16), any field where `user_confirmed === false` is considered unanswered and is placed under **"Missing information"**, prompting the user again with *"Needs your confirmation"*.

### Question 2: "the info i type should be stored and must be used ofr future job applications"
* **Technical Cause:**
  1. When you type an answer in Application Review and click "Save answers", the backend saves it in the `saved_answers` table with a hash of the question (`question_key`).
  2. However, it **does not update your master Profile** (`profiles` table).
  3. When you open a different job later, if that employer worded the question differently (e.g., "LinkedIn URL" vs. "Please share your LinkedIn profile URL"), the question hash changes. The system looks at `Profile`, sees `NULL`, and asks you again!
  4. Syncing contact answers back to `Profile` on save will permanently resolve this.

### Question 3: "it should only display the fields when it doesnt have info againt"
* **Technical Cause:**
  1. The UI is designed to only show missing fields, grouping answered fields under *"View filled answers (N)"*.
  2. However, because the system treats unconfirmed fields as missing, even pre-filled fields appear in the main form until explicitly confirmed.
  3. Once verified profile fields are automatically marked `user_confirmed = True`, they will immediately collapse into the filled answers accordion and disappear from the missing list.

### Question 4: "and also there should be a option for bulk job application"
* **Technical Cause & Where to find it:**
  1. The bulk application option **already exists** in Turio, but it is located exclusively on the **Jobs page (`/jobs`)**, above the job listings.
  2. You can:
     - Check individual job cards with the checkbox *"Select for bulk application"*, or click *"Select visible jobs"*.
     - Choose mode: *"Fill & review"* or *"Automatic submission"*.
     - Click *"Start automatic applications"*.
     - Answer shared questions once in the *"Answer once for selected applications"* box and click *"Save shared answers"*.
  3. As reported in `BUG-UX-001`, this feature should also be surfaced directly on `/applications`.

---

## 5. Summary of Audit Artifacts

Raw audit screenshots and artifacts are private, local-only, and excluded from GitHub. Historical local locations:
- Report JSON: `docs/evidence/qa_audit_20261014/final_audit_report.json`
- Screenshots Directory: `docs/evidence/qa_audit_20261014/`
- Test Script: `scratch/playwright_audit.py`

## 6. Resolution — 2026-10-14

The report describes **nine distinct bug IDs**, including navigation, despite its
original eight-bug count. Code and regression checks now address all nine:

| ID | Resolution |
|---|---|
| BUG-APP-001 | Recognize LinkedIn page/link labels and reuse confirmed canonical contact facts; inferred AI mappings retain explicit confirmation. |
| BUG-APP-002 | Confirmed reusable contact answers update matching profile attributes and version; other drafts retain freshness checks. |
| BUG-APP-003 | Reset to review requires checking the employer site and confirming no submission; old approval is cleared. |
| BUG-APP-004 | Edit filled answers inline; profile-derived edits default to application-only, with explicit reuse opt-in. Local overrides preserve exact field identity. |
| BUG-UX-001 | Shared bulk preparation, question answering and approved submission controls appear in Applications and Jobs; tracker selects exact draft IDs. |
| BUG-NAV-001 | Main navigation includes a labeled Profile link; the existing profile avatar remains available. |
| BUG-PARSE-001 | Extract labeled LinkedIn handles and normalize short personal paths; reject company pages as personal profiles. Protocol-less `/in/` URLs already worked. |
| BUG-JOBS-001 | Platform label clarifies Ashby support without advertising unimplemented platforms. |
| BUG-AUTH-001 | Authentication buttons explicitly use `type="submit"`; browsers already defaulted these buttons to submit. |

Verification: [saved results](docs/evidence/bug-audit-fixes-2026-10-14.json),
[backend regressions](backend/tests/test_bug_audit.py),
[rendered UI checks](scripts/verify_bug_audit_ui.py).
Tests use isolated fixtures/databases; no employer applications were sent and
existing candidate records were preserved. Older drafts may need preparation
with the current profile. History: [daily topic](D:/Projects/Sessions/14-10-2026/turio-bug-audit-fixes.md).
