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
