# CLAUDE.md — Turio Engineering Controller

## Purpose

This file is the **execution contract** for Claude Code / coding agents working on Turio.

The goal is to build the project with **minimum token waste**, clear checkpoints, reproducible work, and no accidental scope expansion.

## 1. Non-negotiable rules

1. **Do not rewrite completed work unless requested.**
2. **Do not read every documentation file for every task.**
3. Read only:
   - `README.md` for project orientation.
   - `PROJECT_SPEC.md` for requirements.
   - the domain file(s) matched to the current task in §2's table below.
   - `PROGRESS.md` for current status.
4. Before coding, inspect the existing implementation. Never recreate working code from assumptions.
5. Before changing architecture, update the relevant ADR and architecture file.
6. Before marking anything complete, run the smallest useful test and record evidence in `PROGRESS.md`.
7. Never invent metrics, dataset statistics, or automation success rates.
8. Never send final application submissions without an explicit user-approval checkpoint.
9. Never ask the user for profile information that is already present in the database.
10. Prefer deterministic logic over LLM reasoning when a normal parser, validator, selector, or database query can perform the task.
11. Use an LLM only where language reasoning materially improves the result.
12. Keep prompts short and task-specific.
13. Do not paste large files into prompts when a file path or targeted read is enough.
14. Avoid repeated re-analysis of unchanged data.
15. Cache expensive model outputs where safe and useful.
16. Keep third-party website automation isolated behind an adapter/interface.

## 2. Task type → doc to read

Use this table to satisfy rule 3 above. Read only the row that matches the current task, plus `README.md` and `PROGRESS.md`.

| Task type | Doc(s) to read |
|---|---|
| Auth / login / tokens | `AUTH.md`, `DATABASE.md` §users/refresh_tokens |
| Backend skeleton / routing | `BACKEND.md`, `SYSTEM_DESIGN.md` §6 |
| Database schema / migrations | `DATABASE.md`, `ADR.md` |
| API contract / routes | `API_SPEC.md` |
| Resume upload / parsing | `BACKEND.md` §5, `DATA_PIPELINE.md` §1 |
| Job ingestion / dataset | `DATASET.md`, `DATA_PIPELINE.md` §2 |
| Matching / ranking / SBERT | `AI_MATCHING.md`, `DATA_PIPELINE.md` §3 |
| Application agent / state machine | `AGENT_ARCHITECTURE.md`, `APPLICATION_AUTOMATION.md` |
| Browser automation / Ashby | `APPLICATION_AUTOMATION.md`, `SUPPORTED_COMPANIES.md` |
| Frontend screen / component | `FRONTEND.md`, `DESIGN_SYSTEM.md` |
| Security / privacy question | `SECURITY_PRIVACY.md`, `AUTH.md` |
| Deployment / infra | `DEPLOYMENT.md` |
| Tests | `TESTING.md` |
| Evaluation / metrics | `EVALUATION.md`, `DATASET.md` §7–9 |
| Multimodal experiment | `MULTIMODAL_FUSION.md` |
| Edge optimization experiment | `EDGE_OPTIMIZATION.md` |
| Token/cost concern | `TOKEN_BUDGET.md` |

If a task spans two rows (e.g. "add resume upload endpoint" touches both Backend and Data Pipeline), read both listed docs — but nothing outside this table.

## 3. Source-of-truth hierarchy

When documents disagree:

```text
1. Current code + tests
2. PROJECT_SPEC.md
3. SYSTEM_DESIGN.md / DATABASE.md / AGENT_ARCHITECTURE.md
4. Other domain docs
5. Old notes
6. General assumptions
```

If a conflict cannot be resolved from evidence, stop and record an ADR instead of silently deciding.

## 4. Task execution protocol

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
Read only the relevant section of:
- `PROGRESS.md`
- one domain specification
- existing code files needed for the change

### DEFINE
Write a one-line task statement before coding.

### INSPECT
Find the existing entry point, interfaces, tests, and data flow.

### IMPLEMENT
Make the smallest coherent change.

### TEST
Run focused tests first. Run broader tests only after the focused tests pass.

### RECORD
Update:
- `PROGRESS.md`
- relevant evidence/metrics
- ADR only if a design decision changed

### STOP
Do not continue into another feature automatically.

## 5. Token budget policy

The project has a very limited external model budget.

### Budget-saving rules

- Prefer Python/TypeScript code over repeated natural-language reasoning.
- Prefer one compact analysis pass over many speculative passes.
- Do not ask the model to summarize files that the agent can directly inspect.
- Keep prompts under the minimum length needed to execute the task.
- Reuse parsed resume/profile data.
- Reuse cached embeddings.
- Batch embedding work.
- Cache job normalization results.
- Do not regenerate explanations when the source facts did not change.
- Use small models or deterministic code for extraction/validation when quality is sufficient.
- Use the expensive model only for ambiguous or genuinely generative tasks.
- Do not send the entire job dataset to an LLM.

## 6. Agent safety rules

The application agent must:

- Operate only on supported websites/workflows.
- Use verified user profile data.
- Preserve the user's facts.
- Never fabricate employment, education, skills, compensation, work authorization, or other personal data.
- Never infer sensitive facts when the form requires an explicit answer.
- Stop when required information is genuinely unavailable.
- Stop before final submission unless the user has explicitly approved the final action.
- Record application events and failures.

## 7. Browser-agent recovery

When automation fails:

```text
Detect failure
→ Capture URL/state/error
→ Retry only if the failure is transient
→ Re-inspect page
→ Try supported alternative selector/path
→ Stop after bounded retries
→ Record failure
```

Never loop indefinitely.

## 8. Definition of done

A task is done when:

- code is implemented,
- focused tests pass,
- acceptance criteria are met,
- evidence is recorded,
- progress is updated,
- no known regression is introduced.

## 9. Current next task pointer

Always use `PROGRESS.md` to determine the next unfinished task.

Do not invent the next task from memory.
