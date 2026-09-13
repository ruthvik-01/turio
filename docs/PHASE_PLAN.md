# Turio — Phase Execution Plan

## 0. Purpose

This file exists to stop token waste and scope creep while an AI coding agent builds Turio.

Without this file, an agent tends to: read every doc every session, build several features in one uncontrolled pass, and only discover a broken interface between two features after both are already "done." This file forces the opposite: **one phase at a time, minimum context per phase, a mandatory stop-and-check at the end of every phase, and an explicit compatibility check against the phase before it.**

This file is read alongside `CLAUDE.md`, not instead of it. `CLAUDE.md` governs *how* to work inside a task. This file governs *which phase is active* and *when to stop*.

## 1. Non-negotiable rules for the agent

1. Work on exactly **one phase** at a time, in order. Never start Phase N+1 while Phase N is not marked `[x] VERIFIED` below.
2. At the start of a session, read only:
   - this file (`PHASE_PLAN.md`) — to find the current phase,
   - `PROGRESS.md` — to find the current task inside that phase,
   - the doc(s) named in that phase's **"Docs to read"** row, using `CLAUDE.md` §2's table if unsure.
   Do not read completed phases' docs again — their decisions are already frozen in code, `ADR.md`, and `PROGRESS.md`.
3. Do not re-generate, rewrite, or "improve" a previous phase's code as a side effect of the current phase. If the current phase genuinely requires a change to a previous phase's code or schema, stop and record it as a new `ADR.md` entry first.
4. At the end of a phase, run the **Exit checklist** and the **Compatibility check** for that phase before touching anything in the next phase. Do not skip this because "it probably still works."
5. After the checklist and compatibility check pass, **stop**. Write the phase report (template in §3) into `PROGRESS.md` and wait for the user to confirm before opening the next phase. Do not self-approve and continue.
6. If the exit checklist or compatibility check fails, stay in the current phase. Fix the fault, re-run only the failed checks (not the entire phase), then stop again.
7. If a fault is found that traces back to a *previous, already-verified* phase, do not silently patch it. Record it as a regression in that phase's row in §2, fix it with the smallest possible change, re-run that phase's exit checklist, then resume the current phase.

## 2. Phases

Each phase lists: objective, exact scope, minimum docs to read, deliverables, exit checklist (fault check), and compatibility check (against the immediately preceding phase). Status is tracked with the same legend as `PROGRESS.md`: `[ ]` not started, `[~]` in progress, `[x]` VERIFIED.

---

### Phase 0 — Foundations
**Status:** [x] VERIFIED

**Objective:** A running skeleton that later phases can attach to. No business logic yet.

**Scope:**
- Repository structure per `SYSTEM_DESIGN.md` §6
- FastAPI app boots, PostgreSQL connects
- `/api/v1/health` returns 200
- Next.js frontend shell boots and can call `/health`
- Docker Compose brings up backend + Postgres + frontend

**Docs to read:** `README.md`, `SYSTEM_DESIGN.md` §6, `BACKEND.md` §1–3, `DEPLOYMENT.md`

**Deliverables:** backend/frontend skeleton committed, `docker-compose up` works, `/health` returns 200 end to end.

**Exit checklist:**
- [ ] `/health` returns 200 with a real DB ping, not a hardcoded response
- [ ] Repo folder structure matches `SYSTEM_DESIGN.md` §6 exactly (including `workers/`)
- [ ] No secrets committed; `.env.example` has placeholders only
- [ ] `docker-compose up` succeeds from a clean clone

**Compatibility check:** N/A (first phase).

---

### Phase 1 — Auth
**Status:** [x] VERIFIED

**Objective:** Every route from Phase 2 onward can trust `user_id` in the request context.

**Scope:**
- `users` + `refresh_tokens` migrations
- `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/refresh`, `/api/v1/auth/logout`, `/api/v1/auth/logout-all`
- JWT middleware enforced on all non-`/api/v1/auth`, non-`/api/v1/health` routes

**Docs to read:** `AUTH.md`, `DATABASE.md` §users/refresh_tokens, `API_SPEC.md` §2

**Deliverables:** working register → login → access protected stub route → refresh → logout flow.

**Exit checklist:**
- [ ] Passwords are bcrypt-hashed, never logged, never returned in any response
- [ ] Refresh tokens stored only as hashes; raw token never persisted
- [ ] Refresh token reuse (already-rotated) is detected and revokes the token family
- [ ] A request with no/expired/invalid token on a protected route returns `UNAUTHENTICATED`, not a 500
- [ ] All 5 test cases in `TESTING.md` §2 (Auth section) pass

**Compatibility check against Phase 0:**
- [ ] `/health` still returns 200 unauthenticated (it must stay public)
- [ ] Auth migrations run cleanly on top of Phase 0's schema with no manual fixups

---

### Phase 2 — Resume & Profile
**Status:** [x] VERIFIED

**Objective:** A logged-in user can upload a resume and get a stored, reviewable candidate profile.

**Scope:**
- `POST /resumes`, `GET/PATCH /profiles/me`
- Resume pipeline: validate → checksum → store → extract text → extract entities → user review → persist
- `profiles`, `resumes`, `skills`, `experiences`, `educations`, `projects` tables populated

**Docs to read:** `BACKEND.md` §5, `DATA_PIPELINE.md` §1, `DATABASE.md` (profile-related entities), `API_SPEC.md` §3

**Deliverables:** upload a real resume file, see an extracted profile persisted and editable.

**Exit checklist:**
- [ ] Upload rejects unsupported file types/oversized files with a stable error code, not a crash
- [ ] Re-uploading the same file (same checksum) does not duplicate/reprocess unnecessarily (per `DATA_PIPELINE.md` §5)
- [ ] No fabricated fields — an empty resume section produces `null`/empty, never an invented value
- [ ] User can edit extracted fields and the edit is what gets used later, not the raw extraction

**Compatibility check against Phase 1:**
- [ ] `/resumes` and `/profiles/me` are rejected with `UNAUTHENTICATED` when called without a token
- [ ] Profile is correctly scoped to `user_id` from the token, not a client-supplied id — attempting to fetch another user's profile returns `FORBIDDEN`

---

### Phase 3 — Job Dataset & Ingestion
**Status:** [~] — built; verification against the composed stack in progress

**Objective:** A populated, deduplicated, queryable job database.

**Scope:**
- Stapply dataset import → normalize → deduplicate → store
- `GET /jobs`, `GET /jobs/{job_id}`, `POST /jobs/refresh`
- `jobs`, `job_sources` tables

**Docs to read:** `DATASET.md`, `DATA_PIPELINE.md` §2, `API_SPEC.md` §4

**Deliverables:** job list queryable via API, re-running the import does not duplicate records.

**Exit checklist:**
- [ ] Re-running ingestion on the same source data changes nothing (idempotent via `source + external_id`)
- [ ] Malformed/missing fields in source data are stored as explicit `null`, not skipped or guessed
- [ ] Content hash changes correctly trigger reprocessing; unchanged records are skipped

**Compatibility check against Phase 2:**
- [ ] Job routes are correctly gated by auth like every other non-`/auth` route (a job feature is an easy place to accidentally forget the dependency)
- [ ] No job-ingestion code accidentally touches `profiles`/`resumes` tables

---

### Phase 4 — Matching & Ranking
**Status:** [ ]

**Objective:** Given a profile and the job database, produce an explainable ranked list.

**Scope:**
- Candidate/job text representations, SBERT embeddings, cosine similarity
- Structured scores (skill/education/experience/location)
- Final score + ranking + explanation payload
- `POST /matches`, `GET /matches`, `GET /matches/{match_id}`
- Keyword and TF-IDF baselines for comparison

**Docs to read:** `AI_MATCHING.md`, `DATA_PIPELINE.md` §3, `API_SPEC.md` §5

**Deliverables:** a real profile returns a ranked, explained job list; baseline comparison numbers exist.

**Exit checklist:**
- [ ] Score weights are stored in a config, not hardcoded inline
- [ ] Every explanation only cites evidence actually present in the stored profile/job data (no fabricated skill claims)
- [ ] Embeddings are cached by `profile_version`/`content_hash` — recomputation only happens when inputs change
- [ ] Same profile + same job database + same config produces the same ranking (reproducible)

**Compatibility check against Phase 3:**
- [ ] Matching reads jobs exclusively through the Phase 3 job repository/API — no direct ad-hoc queries bypassing normalization
- [ ] A job added after Phase 3 (via `/jobs/refresh`) shows up in matching without a manual step

---

### Phase 5 — Application Intelligence
**Status:** [ ]

**Objective:** For a selected job, produce a filled-but-unsubmitted application ready for human review.

**Scope:**
- Application state machine (`AGENT_ARCHITECTURE.md` states through `REVIEW`, not `SUBMIT`)
- Form-field schema, profile-to-form mapping, missing-field collection, generative answer drafting
- `applications`, `application_fields`, `application_answers`, `application_events` tables
- `POST /applications` through `.../review` (not `.../approve-submit` yet)

**Docs to read:** `AGENT_ARCHITECTURE.md`, `APPLICATION_AUTOMATION.md` §2–6, `DATABASE.md` (application entities), `API_SPEC.md` §6

**Deliverables:** a mock/sample form gets correctly mapped, missing fields are asked for exactly once, a review payload is produced.

**Exit checklist:**
- [ ] Known profile data is never re-asked (profile precedence per `DATABASE.md` §5 is enforced)
- [ ] Sensitive fields (work authorization, sponsorship, demographic) are only ever filled from explicit stored answers, never inferred
- [ ] Generative answers are clearly marked as drafts pending user approval, never auto-finalized
- [ ] All state transitions match the `AGENT_ARCHITECTURE.md` state diagram exactly — no skipped states

**Compatibility check against Phase 4:**
- [ ] The job being applied to is fetched through the same job data used in matching, not a separate/stale copy
- [ ] The profile used for mapping is the same verified profile from Phase 2, not a re-derived one

---

### Phase 6 — Browser Automation (Ashby)
**Status:** [ ]

**Objective:** The Phase 5 review payload gets filled into a real browser form and submitted only on explicit approval.

**Scope:**
- Browser Use integration, Ashby adapter
- `POST .../start`, `POST .../approve-submit`
- Bounded-retry recovery flow
- One company at a time from the five-company trial set

**Docs to read:** `APPLICATION_AUTOMATION.md`, `SUPPORTED_COMPANIES.md`, `AGENT_ARCHITECTURE.md` §5 (bounded autonomy/retry)

**Deliverables:** at least one company (start with 1Password) has a fully tested, evidenced application run.

**Exit checklist:**
- [ ] Submission never happens without a prior explicit `approve-submit` call from the user
- [ ] Retries are bounded exactly as specified (selector: 2, page refresh: 1, session restart: 1) — no infinite loop possible
- [ ] Failure is recorded in `application_events` with enough detail to diagnose, and the system never claims success on a failed submission
- [ ] Per-company evidence recorded per `SUPPORTED_COMPANIES.md` (job_url, form_schema_version, test_date, success/failure, artifact reference)

**Compatibility check against Phase 5:**
- [ ] The browser agent fills exactly the values approved in the Phase 5 review screen — no re-mapping or re-generation happens inside the browser step
- [ ] Uploading the resume uses the original stored file reference from Phase 2, not a regenerated one

**Repeat this phase once per additional company**, per the expansion rule in `SUPPORTED_COMPANIES.md` (only after the current company is stable).

---

### Phase 7 — Research Extensions
**Status:** [ ]

**Objective:** Satisfy the coordinator-required research scope with measured results.

**Scope:**
- Multimodal fusion experiment (`MULTIMODAL_FUSION.md`)
- Edge optimization experiment (`EDGE_OPTIMIZATION.md`)
- Original evaluation methodology / Application Readiness Score (`EVALUATION.md`)

**Docs to read:** `MULTIMODAL_FUSION.md`, `EDGE_OPTIMIZATION.md`, `EVALUATION.md`, `DATASET.md` §7–9

**Deliverables:** baseline-vs-improved comparison numbers for each of the three research items, with frozen configs.

**Exit checklist:**
- [ ] Each experiment logs dataset version, model version, config, and metric results per `EVALUATION.md` §7
- [ ] No claimed improvement without a stated baseline and comparison metric
- [ ] Benchmark/test split was frozen before results were generated (no leakage per `DATASET.md` §9)

**Compatibility check against Phase 4/5:**
- [ ] Multimodal fusion is evaluated as an addition to the existing Phase 4 matching pipeline, not a parallel rebuild of it
- [ ] Edge optimization targets only the specific operations named in `EDGE_OPTIMIZATION.md` §2 — it must not change Phase 5's mapping/validation logic's correctness, only its latency profile

---

### Phase 8 — Finalization
**Status:** [ ]

**Objective:** A demo-ready, evaluated, deployed system with report evidence.

**Scope:**
- End-to-end test (Phase 0 → Phase 6 path)
- Performance and security pass
- Deployment to evaluation/demo environment
- Final metrics, screenshots, report, presentation evidence

**Docs to read:** `TESTING.md`, `SECURITY_PRIVACY.md`, `DEPLOYMENT.md`, `EVALUATION.md`

**Deliverables:** one recorded, evidenced, end-to-end run from resume upload to a real tracked application; final report draft.

**Exit checklist:**
- [ ] Full end-to-end path (resume → profile → jobs → matching → ranking → application → review → approved submission → tracking) runs without manual intervention beyond the required user checkpoints
- [ ] Security pass confirms no plaintext secrets, no raw sensitive-field logging, access control enforced everywhere
- [ ] All acceptance criteria in `PROJECT_SPEC.md` §8 are demonstrably met

**Compatibility check against all previous phases:**
- [ ] Nothing in Phases 0–7 was broken by finalization work — re-run each phase's exit checklist at least once, not just the new work

---

## 3. Phase report template

Paste this into `PROGRESS.md` at the end of every phase, filled in, before stopping:

```text
## Phase X report — <name>

Status: VERIFIED / BLOCKED

Exit checklist: <pass/fail per item, one line each>

Compatibility check vs Phase X-1: <pass/fail per item, one line each>

Evidence: <test output / commit hash / screenshot reference>

Known issues carried forward: <none, or list>

Awaiting user confirmation to start Phase X+1.
```

## 4. Token-saving rules specific to phased work

- Never re-read a `[x] VERIFIED` phase's docs in a later phase unless that phase's compatibility check fails.
- Never regenerate a whole file to make one change; use targeted edits.
- When a compatibility check fails, re-run only the failed item, not the entire previous phase's exit checklist.
- Summarize a completed phase in one paragraph in `PROGRESS.md` instead of keeping the full working transcript in context for later phases.
- If a phase must pause mid-way (context limit, blocked task), record exactly which checklist items are done so the next session resumes at the right item instead of restarting the phase.

## 5. Master dependency map

```text
Phase 0 (Foundations)
   └─ Phase 1 (Auth) — needs DB from Phase 0
        └─ Phase 2 (Resume/Profile) — needs user_id from Phase 1
             └─ Phase 3 (Jobs) — independent of Phase 2, but gated by Phase 1 auth
                  └─ Phase 4 (Matching) — needs Phase 2 profile + Phase 3 jobs
                       └─ Phase 5 (Application Intelligence) — needs Phase 2 profile + Phase 4 job selection
                            └─ Phase 6 (Browser Automation) — needs Phase 5 review payload
                                 └─ Phase 7 (Research Extensions) — extends Phase 4 and Phase 5
                                      └─ Phase 8 (Finalization) — needs all previous phases VERIFIED
```

If a phase seems to need something from a phase that hasn't run yet, stop — do not build around it with a shortcut. Record the ordering conflict as an `ADR.md` entry instead.
