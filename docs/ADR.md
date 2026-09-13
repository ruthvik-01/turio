# Turio — Architecture Decision Records

Status values:
- **Accepted** — approved source-of-truth decision.
- **Superseded** — replaced by a later decision.
- **Pending** — decision still requires explicit approval before the dependent phase.

## ADR-001 — Agile iterative SDLC
**Status:** Accepted
**Decision:** Use Agile/iterative development.
**Context:** Multiple technical domains and research requirements need incremental validation.
**Alternatives:** Waterfall; big-bang implementation.
**Reasoning:** Small verified increments reduce integration risk.
**Impact:** Development is governed by `PHASE_PLAN.md` and `SDLC.md`.

## ADR-002 — FastAPI backend
**Status:** Accepted
**Decision:** Use FastAPI for the main backend.
**Reasoning:** Typed schemas, async support and clear API/service boundaries fit the system.
**Impact:** Backend route/service implementation follows `BACKEND.md`.

## ADR-003 — PostgreSQL
**Status:** Accepted
**Decision:** Use PostgreSQL as the application database.
**Reasoning:** Relational integrity, JSONB, concurrency and extension options fit the workload.

## ADR-004 — Browser Use as application-agent layer
**Status:** Accepted
**Decision:** Isolate Browser Use behind the application automation adapter.
**Reasoning:** Browser-specific behavior must not leak into generic matching/domain logic.

## ADR-005 — Initial Ashby-only trial
**Status:** Accepted
**Decision:** Start with 1Password, Linear, Supabase, Vercel and Notion.
**Reasoning:** Controlled application-platform scope reduces automation variance.

## ADR-006 — Persistent profile
**Status:** Accepted
**Decision:** Store verified user information once and reuse it.
**Reasoning:** Users must not repeatedly answer information already known to Turio.

## ADR-007 — Explicit submission approval
**Status:** Accepted
**Decision:** Require user approval immediately before final submission.
**Reasoning:** Prevent accidental/unauthorized submissions.

## ADR-008 — Deterministic before generative
**Status:** Accepted
**Decision:** Prefer deterministic parsing, normalization, mapping and validation whenever sufficient.
**Reasoning:** Lower cost, higher reproducibility and lower hallucination risk.

## ADR-009 — Password + JWT authentication
**Status:** Accepted
**Decision:** Email/password + hashed password + JWT access token + rotating hashed refresh token.
**Reasoning:** Simple MVP auth with strong user isolation and no external IdP dependency.

## ADR-010 — Single frontend source of truth
**Status:** Accepted
**Decision:** `FRONTEND.md` is the only authoritative frontend architecture/visual-direction document. `DESIGN_SYSTEM.md` is token support; `DESIGN_REFERENCE_SOURCE.md` is reference material.
**Context:** Earlier documentation combined two competing frontend ideas.
**Reasoning:** One authority removes ambiguity and prevents accidental redesign during coding.
**Impact:** Frontend work must follow `FRONTEND.md` unless a later ADR explicitly changes it.

## ADR-011 — Approved frontend visual direction
**Status:** Accepted
**Decision:** Preserve the current approved cream/green, rounded, restrained-glass, editorial-display + sans-UI direction shown in the current approved references.
**Reasoning:** This is the user-approved direction and must remain frozen until explicitly changed.
**Impact:** No new frontend design concepts are to be introduced by agents.

## ADR-012 — Top navigation instead of permanent desktop sidebar
**Status:** Accepted
**Decision:** Use the approved top-navigation model on desktop; do not introduce a permanent left sidebar.
**Reasoning:** This is part of the approved dashboard/reference structure.

## ADR-013 — Brand asset is authoritative
**Status:** Accepted
**Decision:** Use the supplied Turio logo asset as the brand source. Do not re-typeset the wordmark.
**Reasoning:** A near-match font recreation is not an acceptable substitute for the actual mark.

## ADR-014 — Typography roles
**Status:** Accepted
**Decision:** Three distinct roles: logo asset, editorial display typography, Inter/system sans UI typography.
**Reasoning:** Separates brand, editorial hierarchy and functional interface text.

## ADR-015 — Application status vs outcome
**Status:** Accepted
**Decision:** `applications.status` represents Turio's automation/application pipeline; `applications.outcome` represents recruiter-side result.
**Reasoning:** This makes dashboard/tracking metrics derivable without conflating automation state with recruitment outcome.

## ADR-016 — Canonical API pathing
**Status:** Accepted
**Decision:** Every API route is written with the `/api/v1` prefix in `API_SPEC.md`.
**Reasoning:** Eliminates disagreement between backend route grouping and route examples.

## ADR-017 — Idempotency persisted in application events
**Status:** Accepted
**Decision:** Persist idempotency keys for retry-sensitive application events and use request idempotency at application creation/submission approval.
**Reasoning:** Prevent duplicate application/submission side effects.

## ADR-018 — Evaluation annotations are a separate table
**Status:** Accepted
**Decision:** Use `evaluation_annotations` for research labels rather than mixing research judgments into production job/application tables.
**Reasoning:** Keeps evaluation data versioned and separate from live product state.

## ADR-019 — Profile version for cache invalidation
**Status:** Accepted
**Decision:** `profiles.version` increments when relevant profile data changes and participates in cache keys.
**Reasoning:** Makes profile-dependent cached results invalidatable without expensive global recomputation.

## ADR-020 — Keep current `master` until safe remote migration
**Status:** Accepted
**Decision:** Use `master` as the current integration branch because the existing `origin/main` has unrelated history. Do not force-push to overwrite it.
**Reasoning:** Protects existing remote history. A later branch migration must be deliberate and verified.

## ADR-021 — Brand color derivation
**Status:** Accepted
**Decision:** UI greens adjacent to the Turio mark must derive from the brand forest family rather than an unrelated competing green.
**Reasoning:** Prevents visually inconsistent green values around the logo and primary product identity.

## ADR template

### ADR-XXX — Title
**Status:** Pending
**Decision:**
**Context:**
**Alternatives:**
**Reasoning:**
**Impact:**
**Evidence:**
