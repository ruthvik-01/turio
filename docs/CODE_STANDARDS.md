# Turio — Code Standards

## 0. Purpose

`CLAUDE.md` governs what to build and when to stop. `TESTING.md` governs how it's verified. This file governs **how the code itself is written** — so that every feature is (a) no bigger than it needs to be, and (b) built so that when it breaks, the cause is obvious in seconds, not discovered by adding print statements after the fact.

This applies to every commit described in `GIT.md`, not just "important" code. There is no separate "quick script, doesn't need to be clean" tier in this project.

## 1. Write only the code the current task needs

This is the single most-violated rule in student/AI-generated codebases, so it's stated first.

- Implement exactly what the current `PROGRESS.md` task requires. Do not add a config system, plugin architecture, extra abstraction layer, or "flexibility for later" that no current task needs.
- **Rule of three:** don't extract a shared function/class until the same logic is genuinely needed a third time. Two occurrences can stay duplicated a little longer than feels comfortable — a wrong abstraction is more expensive to undo than a small duplication.
- No unused imports, unused function parameters, unused config flags, or commented-out code left "just in case." Delete it. Git history already remembers it.
- No speculative error handling for cases that cannot occur given the current call path. Handle the errors that can actually happen; add more when a new caller actually introduces a new failure mode.
- If a function needs more than ~4 parameters or a file grows past ~300 lines, that's a signal to reconsider the shape of the code — not a hint to keep going and add a fifth parameter.
- Before adding a new dependency/library, check whether the standard library or an already-used dependency can do it. Every new dependency is something that can break, needs updating, and needs justifying in `ADR.md` if it's a meaningful one (per `ADR.md`'s existing pattern).

## 2. Build every feature to be debuggable by construction

The goal: when something breaks, the log line or error message alone should point at the cause, without needing to reproduce the bug locally first.

### Fail fast, fail loud
- Validate inputs at the boundary (API request, file upload, external API response) and reject immediately with a specific error, not several layers deeper with a confusing stack trace.
- Never use a bare `except:` / `catch (e) {}` that swallows an error silently. If you catch an exception, either handle it meaningfully or re-raise it with added context.

```python
# Bad — swallows the real cause
try:
    profile = extract_profile(resume_text)
except Exception:
    profile = None

# Good — fails loud with context, matches BACKEND.md error codes
try:
    profile = extract_profile(resume_text)
except ExtractionError as e:
    raise ProfileExtractionFailed(
        resume_id=resume.id,
        parser_version=PARSER_VERSION,
        cause=str(e),
    ) from e
```

### Every error carries context, not just a message
Every raised/logged error should include enough identifiers to trace it without asking "which user, which request, which job?" Reuse the identifiers `BACKEND.md` §12 already defines:

```text
request_id
user_id (where authorized)
application_id (where relevant)
agent_run_id (for agent execution)
```

A log line like `"extraction failed"` is not acceptable. A log line like `"extraction failed: resume_id=<id> parser_version=<v> reason=<specific reason>"` is.

### Structured logs, not print statements
- No `print()` / `console.log()` left in committed code. Use the project's logger.
- Log as structured fields (JSON-style key/value), not a single concatenated sentence — this is what actually lets you grep/filter logs by `user_id` or `agent_run_id` later.
- Log at the right level: `error` for things that need attention, `warning` for recovered/degraded situations, `info` for normal lifecycle events (e.g. `RESUME_UPLOADED`), `debug` for detail only needed while actively investigating something.

### Every agent/browser step records what it was doing when it failed
This project already has `application_events` and `agent_runs` tables (`DATABASE.md`) precisely for this. Every state transition in `AGENT_ARCHITECTURE.md`'s state machine must write an event on both success and failure — never fail silently and leave the state ambiguous. This is what makes `APPLICATION_AUTOMATION.md` §8's failure handling (stage, site, diagnostic id) possible at all instead of theoretical.

### Assertions for "this should be impossible"
Where a state should be logically impossible if earlier code is correct (e.g. an `application` reaching `SUBMIT` without a `REVIEW` event), assert it rather than silently proceeding. An assertion that fires loudly during development is far cheaper than a corrupted record discovered in production.

## 3. Naming and structure

- Names describe what something *is* or *does*, not how it's implemented: `normalize_job_title()`, not `helper2()` or `do_the_thing()`.
- One function does one job. If describing a function needs the word "and," it's probably two functions.
- Match the layering already defined in `BACKEND.md` §2 (routes → schemas → services → repositories → DB). Business logic does not live in a route handler; DB queries do not live in a service.
- Use type hints (Python) / strict TypeScript types everywhere. A function signature should tell you what it needs and returns without opening the body.
- Comments explain *why*, not *what* — the code already says what it does. `# retry once: Ashby occasionally 500s on first load` is a useful comment; `# loop through fields` above a for-loop is not.

## 4. Every feature ships with the smallest test that would have caught its own bug

This connects directly to `TESTING.md` and `CLAUDE.md`'s TEST step:

- Before marking a feature done, write the one focused test that would fail if the bug you were worried about were reintroduced. Not a broad end-to-end test — the smallest one that isolates the actual risk.
- If a bug is found and fixed, add a regression test for that exact bug before committing the fix (`fix(...)` commit in `GIT.md` should usually come with a matching `test(...)` change, or be in the same commit).

## 5. Pre-commit checklist

Run through this before every `git commit` described in `GIT.md` — it's the practical, code-level companion to that file's commit discipline:

- [ ] No `print()`/`console.log()` debug statements left in
- [ ] No commented-out code, no unused imports/variables
- [ ] No bare/silent exception handlers
- [ ] Every raised error includes enough identifiers to trace it (§2)
- [ ] No new abstraction/config/parameter that isn't used by the current task
- [ ] Function/file sizes are reasonable (§1); nothing was force-fit into an existing giant file
- [ ] A focused test exists for the new behavior or the fixed bug
- [ ] No secrets, credentials, or `.env` values in the diff

## 6. Anti-patterns to actively avoid

```text
Catch-all exception handlers that hide the real error
"Just in case" parameters/flags nothing currently uses
Copy-pasted blocks instead of extracting after the 3rd repeat
Deep nesting (4+ levels) instead of early returns/guard clauses
Magic numbers/strings instead of named constants
God functions that validate, transform, call the DB, and format the response all in one
Debug print statements committed instead of removed or converted to proper logs
Rewriting working code from a previous phase "while I'm in there" (see PHASE_PLAN.md §1.3)
```

## 7. How this fits with the rest of the docs

```text
PHASE_PLAN.md   → which phase, what's in scope
CLAUDE.md       → task protocol, what to read, when to stop
CODE_STANDARDS.md (this file) → how the code inside that task is written
TESTING.md      → how it's verified
GIT.md          → when/how it's committed and merged
```

A feature isn't "done" per `CLAUDE.md`'s Definition of Done until it also satisfies this file's §5 checklist — professional code, not just working code, is part of the exit bar for every task, not an extra step for later.
