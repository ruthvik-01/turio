# CLAUDE.md — Turio Engineering Controller

## Purpose

This file is the execution contract for Claude Code and other coding agents working on Turio.

The priority is:
- understand the repository before changing it,
- implement only the active task,
- minimize model/token waste,
- preserve phase boundaries,
- preserve user-review and submission safety boundaries.

## 1. Non-negotiable rules

1. Do not rewrite completed work unless requested.
2. Do not read every documentation file for every task.
3. Before coding, inspect current code/tests; never recreate code from assumptions.
4. Before changing architecture, update `ADR.md` and the owning architecture document.
5. Never mark work complete without focused verification evidence.
6. Never invent metrics, dataset statistics, model results, or success rates.
7. Never submit an application without an explicit user-approval checkpoint.
8. Never ask the user for profile information already present in the database.
9. Never fabricate employment, education, skills, compensation, authorization, sponsorship, or other personal data.
10. Prefer deterministic code over LLM reasoning when deterministic logic is sufficient.
11. Keep prompts short and task-specific.
12. Do not paste large files into prompts when the agent can inspect them directly.
13. Cache expensive model outputs when safe.
14. Isolate third-party automation behind adapters.
15. Do not introduce a new frontend direction unless the user explicitly asks for it.

## 2. Before any implementation

Read:

```text
PROGRESS.md
→ PHASE_PLAN.md (if phase boundary/order matters)
→ domain docs for the active task
→ relevant existing code/tests
```

`DOCS_MANIFEST.md` tells you what each `.md` file is for and which document owns each concern.

## 3. Source-of-truth hierarchy

When documents disagree:

```text
1. Current code + tests
2. PROJECT_SPEC.md
3. SYSTEM_DESIGN.md / DATABASE.md / AGENT_ARCHITECTURE.md
4. FRONTEND.md for frontend structure/visual direction
5. API_SPEC.md for API contract
6. Other domain docs
7. Old/reference material
```

Do not resolve a consequential conflict silently. Record an ADR first.

## 4. Task protocol

Every implementation task follows:

```text
READ
→ DEFINE
→ INSPECT
→ IMPLEMENT
→ TEST
→ RECORD
→ STOP
```

### READ
Read only the minimum relevant sections of the owning documents.

### DEFINE
State the task in one sentence.

### INSPECT
Locate the actual entry point, interfaces, tests, and data flow.

### IMPLEMENT
Make the smallest coherent change required by the active task.

### TEST
Run focused tests first; broaden only after they pass.

### RECORD
Update `PROGRESS.md` with evidence. Update `ADR.md` only when a real design decision changes.

### STOP
Do not automatically continue to another task or phase.

## 5. Frontend control

`FRONTEND.md` is the single frontend source of truth.

`DESIGN_SYSTEM.md` provides tokens only.

`DESIGN_REFERENCE_SOURCE.md` is raw reference material only.

Do not invent:
- new navigation,
- new layout systems,
- new colors,
- new animation systems,
- new decorative concepts,
- new screens,

unless explicitly requested by the user.

## 6. Token budget policy

- Prefer direct file inspection over LLM summarization of files.
- Never send the entire dataset to a model.
- Reuse parsed resumes/profiles.
- Batch embeddings.
- Cache unchanged embeddings and normalized jobs.
- Do not regenerate explanations when source evidence is unchanged.
- Use the expensive model only for genuinely ambiguous/generative work.
- Avoid repeated analysis of unchanged context.

## 7. Agent safety

The Application Agent must:
- operate only on supported workflows,
- use verified profile data,
- ask only for genuinely missing information,
- stop on ambiguous sensitive facts,
- stop before final submission,
- record meaningful state transitions/failures.

## 8. Definition of done

A task is complete only when:
- the implementation is present,
- focused tests pass,
- acceptance criteria are met,
- evidence is recorded,
- `PROGRESS.md` is updated,
- no known regression is introduced.

## 9. Current task pointer

Use `PROGRESS.md`. Do not invent the next task from memory.
