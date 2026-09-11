# Turio — Architecture Decision Record

## ADR-001 — Agile iterative SDLC

**Decision:** Use Agile/iterative development.

**Reason:** Multiple technical domains and research requirements must be validated incrementally.

---

## ADR-002 — FastAPI backend

**Decision:** Use FastAPI rather than Flask for the main backend.

**Reason:** Typed schemas, async support, API documentation, and clean service boundaries fit the project.

---

## ADR-003 — PostgreSQL

**Decision:** Use PostgreSQL rather than SQLite/MySQL for the main application database.

**Reason:** Better fit for relational integrity, JSONB fields, concurrent use, and future scaling.

---

## ADR-004 — Browser Use as application-agent layer

**Decision:** Isolate Browser Use behind an application automation adapter.

**Reason:** Browser automation should not leak into matching/domain logic and should be replaceable.

---

## ADR-005 — Initial Ashby-only trial

**Decision:** Start with five Ashby companies.

**Reason:** Controlled experimentation over one application platform reduces automation variability.

---

## ADR-006 — Persistent profile

**Decision:** Store verified user information once and reuse it.

**Reason:** The user should not repeatedly answer questions that are already known.

---

## ADR-007 — Explicit submission approval

**Decision:** Require user approval immediately before final submission.

**Reason:** Prevent accidental or unauthorized application submission.

---

## ADR-008 — No LLM for deterministic tasks

**Decision:** Prefer deterministic code for parsing, normalization, field mapping, validation, and database operations.

**Reason:** Lower cost, reproducibility, speed, and reduced hallucination risk.

---

## ADR-009 — Password + JWT authentication

**Decision:** Use email/password login with bcrypt password hashing, short-lived JWT access tokens, and rotating opaque refresh tokens stored hashed in the database. See `AUTH.md` for full detail.

**Reason:** No external identity provider is required for the MVP. This is simple to implement and test end-to-end, does not block the Ashby browser-automation work, and leaves room to add OAuth later via an additive `auth_provider` column rather than a redesign.

---

## ADR template

### ADR-XXX — Title

**Decision:**

**Context:**

**Alternatives:**

**Reasoning:**

**Impact:**

**Evidence:**
