# Turio — Data Pipeline

## 1. Resume pipeline

```text
Upload
→ Validate file
→ Compute checksum
→ Store original
→ Extract text
→ Normalize text
→ Detect sections
→ Extract entities/facts
→ Normalize fields
→ User review
→ Persist verified profile
```

Current ingestion extracts and validates locally before object/profile persistence;
`rules-v6-heading-spacing` retains positional row/column/page order, recognizes
exact known letter-spaced heading aliases, preserves grouped skill qualifiers
and multiline role/company evidence, filters decorations
and repeated headers, and copies source-stated supplemental facts. No fixed
resume template or Google service. Bounded unreadable text pages fail safely;
scanned images need searchable text supplied outside this pipeline.

Optional Jev Choice assistance classifies unfamiliar headings from bounded
source excerpts with per-action consent, never PDF bytes. Suggestions are not
automatically persisted: accept into the editor and save with the expected
profile version. Account email and sensitive declarations are not inferred.
Evidence: `evidence/resume-layouts-2026-10-13.json`; ADR-044.

## 2. Job pipeline

```text
Source
→ Fetch/import
→ Validate
→ Normalize
→ Deduplicate
→ Parse requirements
→ Normalize skills
→ Generate embeddings
→ Store
```

## 3. Matching pipeline

```text
Candidate profile
→ Candidate text representation
→ Embedding

Job
→ Job text representation
→ Embedding

Candidate embedding + Job embedding
→ cosine similarity

Structured profile/job fields
→ deterministic feature scores

All signals
→ final score
→ ranking
```

## 4. Caching

Cache:

- parsed resume text by file checksum,
- extracted profile by parser version,
- job normalization by content hash,
- job embeddings by model version + content hash,
- candidate embeddings by profile version,
- explanation inputs by match/result version.

## 5. Reprocessing triggers

Reprocess only when:

- file checksum changes,
- parser version changes,
- extraction rules change,
- model version changes,
- job content hash changes,
- user explicitly edits verified profile data.


## Cache contract

Cache keys that depend on candidate state must include `profile.version`. Job-dependent caches must include the job content hash or equivalent stable version. The concrete cache technology is implementation-defined and should be introduced only when required by the active phase.
