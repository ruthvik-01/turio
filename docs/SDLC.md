# Turio — SDLC

## Methodology

Use an **Agile iterative SDLC**.

Reason: Turio combines NLP, recommendation, browser automation, database workflows, and research evaluation. Several requirements also need experimental refinement.

## Lifecycle

```text
1. Requirements
        ↓
2. Architecture & Design
        ↓
3. Prototype
        ↓
4. Small Increment Implementation
        ↓
5. Focused Testing
        ↓
6. Measurement / Evaluation
        ↓
7. Review
        ↓
8. Next Increment
        ↺
```

## Development increments

### Increment 1
Project skeleton + backend health + frontend shell + database connection.

### Increment 2
Resume upload + text extraction.

### Increment 3
Candidate profile extraction + persistence.

### Increment 4
Dataset ingestion + normalized jobs.

### Increment 5
SBERT embeddings + semantic matching.

### Increment 6
Ranking + explanations.

### Increment 7
Application-form inspection + field extraction.

### Increment 8
Profile-to-form mapping + missing-information handling.

### Increment 9
Browser Use integration for supported Ashby workflows.

### Increment 10
User review + approval + submission + tracking.

### Increment 11
Multimodal fusion.

### Increment 12
Edge optimization.

### Increment 13
Original evaluation framework.

### Increment 14
Hardening, testing, deployment, documentation.

## Gate rule

Do not start the next increment until the current increment has:

- implementation,
- focused tests,
- evidence,
- progress entry.

## Change control

Any change to architecture, data model, or core scoring should be recorded in `ADR.md`.
