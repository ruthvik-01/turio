# Turio — Git Workflow

## 1. Current repository state

The documentation review found that the repository currently uses `master` as its existing branch and that `origin/main` has unrelated history.

**Do not force-push or rewrite the remote history just to rename the branch.**

For the current implementation phase, `master` is the integration branch until a deliberate repository migration is approved.

## 2. Branching

Use one working branch per feature/phase:

```text
master
├── phase-0-foundation
├── phase-1-auth
├── phase-2-resume-profile
├── phase-3-jobs
├── phase-4-matching
├── phase-5-application-intelligence
├── phase-6-browser-automation
├── phase-7-research
└── phase-8-finalization
```

Feature branches may be created from the active phase branch when a task is large enough to justify one.

## 3. Commit discipline

Use Conventional Commits:

```text
feat:
fix:
docs:
test:
refactor:
chore:
```

One coherent change per commit.

## 4. Phase merge gate

A phase branch may merge into `master` only after:
- `PHASE_PLAN.md` exit checklist passes,
- compatibility check passes,
- focused tests pass,
- evidence is recorded in `PROGRESS.md`.

## 5. Remote branch migration

If the team later wants `main` instead of `master`, perform an explicit migration only after verifying remote history and team access.

Do not use `git push --force` to overwrite an unrelated `origin/main`.

## 6. Before every commit

Run:
- focused tests,
- lint/type checks applicable to changed code,
- `git diff --check`,
- secret check where available.

Record meaningful verification evidence in `PROGRESS.md`.
