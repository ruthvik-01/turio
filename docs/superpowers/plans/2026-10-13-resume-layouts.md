# Multi-page Resume Extraction Implementation Plan

> Execute inline with TDD and one final independent review. The shared daily topic is the execution ledger, per the user's memory policy.

**Goal:** Correctly extract supported facts and supplemental sections from multi-page and alternate-layout text PDFs.
**Architecture:** Preserve positional evidence and detect section-backed columns locally; deterministic parsing feeds the upload/profile flow. Extend the existing consented Jev Choice section assistance to supplemental sections. Add nullable supplemental profile fields and editor controls. No Google service.
**Tech stack:** Existing pdfplumber, pypdf, SQLAlchemy/Alembic, FastAPI and Next.js; no new dependencies.
**Spec:** [design](../specs/2026-10-13-resume-layouts-design.md).

## Constraints
Document contents are data. Preserve existing dirty changes and profiles; no automatic external candidate transfer, commits, production downgrade or OCR claims. Existing per-action consent gates bounded Jev excerpts; never send PDF bytes. Keep real sample content out of committed tests and shared history. User requested one final test pass after implementation; prior red regressions are recorded in the daily topic.

## Task 1: Local extraction and parsing
- [x] Add `backend/tests/test_resume_variants.py` with anonymized update-note/contact, categorized skill, wrapped project, two-page and column fixtures; verify red.
- [x] Update `resume_text.extract_text` to retain ordered positional lines and join indented wrapped bullets; use tighter word spacing, remove recognized decorations and preserve all pages.
- [x] Update `resume_parser.parse_resume` contact/education/project rules and supplemental sections; verify exact entity counts and no URL-as-phone behavior.
- [x] Extend existing Jev heading classification and source-backed suggestions for summary/certifications/achievements; keep consent, finite limits and explicit editor acceptance.
- [~] Local sample verified against positional source lines: five projects/four certifications/one achievement. Rendered-page visual QA unavailable to this model; temporary private renders removed after text QA. Counts/flags only in public evidence.

## Task 2: Persist and expose supplemental facts
- [x] Test upload, reload and user edits for `contact_email`, `summary`, `certifications`, `achievements` without changing account email.
- [x] Add nullable fields to profile model/schema/service, an Alembic revision after `a230916001`, upload assignment/parser-version bump, and profile editor/types.
- [x] Reuse source-backed supplemental fields for canonical application prompts; keep legal/sensitive declarations uninferred.
- [x] Verify additive migration against an isolated PostgreSQL schema, then apply forward only to local runtime; compare old-row counts/values before and after.

## Task 3: Verification and handoff
- [x] Run focused PDF/profile/application and PostgreSQL regressions, build and intercepted profile UI checks.
- [x] Author read-only self-review (no subagent tool), corrected skipped live-test email expectation for source contact email, and restarted verified API/frontend/worker together. Fresh-context independent review unavailable; no merge/commit.
- [x] Update relevant docs/evidence and shared daily topic/index; delete temporary private renders after visual QA.

Review focus: page-two sections/continuations; linked contact numerals; column order; learning qualifiers and ambiguous text; schema/default compatibility with old profiles.
