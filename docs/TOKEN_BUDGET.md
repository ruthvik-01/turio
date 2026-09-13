
# Turio — Token Budget and Cost Control

## 1. Goal

The project is being developed under a very small external-model budget(like a dollar deepseek tokens). Optimize for **useful work per token**, not maximum model usage.

## 2. Model routing

### Deterministic code first

Use normal code for:

- file parsing,
- regex,
- schema validation,
- database queries,
- field selectors,
- score arithmetic,
- status transitions.

### Small/cheap model where enough

Use for:

- simple classification,
- normalization,
- concise extraction.

### Strong model only when needed

Use for:

- ambiguous form questions,
- high-quality written-answer drafts,
- difficult reasoning,
- research/evaluation interpretation.

## 3. Cache

Cache by stable input:

```text
resume_checksum + parser_version
job_hash + embedding_model
profile_version + job_id
application_id + form_hash
```

## 4. Batch

Batch:

- embeddings,
- job normalization,
- evaluation runs.

## 5. Prompt discipline

Every prompt should include only:

```text
task
+
required context
+
constraints
+
expected output
```

Do not include:

- project history,
- unrelated files,
- repeated architecture,
- full datasets.

## 6. Prompt/context cache-hit discipline

This is different from §3 (caching *results* by checksum). This section is about avoiding **cache misses on the LLM API's own prompt cache** — every miss means the model reprocesses the full prompt from scratch instead of reusing already-processed tokens, which costs both money and latency.

### Structure every prompt stable-part-first, variable-part-last

```text
[stable] system instructions / role definition
[stable] tool definitions
[stable] large reference context (schemas, examples, static docs)
─────────────────────────────────────────────
[variable] this request's specific data
[variable] this request's specific question
```

The API can only reuse the prefix that is **byte-for-byte identical** to a previous call. Anything variable placed early in the prompt invalidates the cache for everything after it, even if the rest of the prompt is unchanged.

### Common ways this project could break its own cache without noticing

- Inserting the current timestamp, a request id, or `user_id` into the system prompt instead of into the trailing user turn — this alone silently makes every single call a full cache miss.
- Reordering tool definitions between calls (e.g. building the tool list from a dict/set without a fixed order).
- Regenerating a "context summary" with slightly different wording on every call instead of reusing a stored, versioned version of it.
- Mixing prompt-template changes into an unrelated code change — a one-character whitespace change in a static instruction block invalidates the cache for every call using that template until it's redeployed consistently everywhere.

### Minimum viable content to cache

Only mark large, reused, stable blocks for caching (e.g. the resume/profile schema reference sent to the extraction step, the job-normalization instructions, the form-mapping rules) — trivially small prompts aren't worth the cache overhead. Do not cache content that changes every call (per-request user data, per-job descriptions used once).

### Verify, don't assume

Check the API response's cache usage fields (cache read vs. cache creation token counts) after implementing a prompt template. A prompt that "should" cache but shows cache-creation tokens on every call has a hidden variable leaking into the stable prefix — find and move it before assuming the template is correct.

## 7. Structured outputs

Prefer JSON/schema outputs over long prose when the model is acting as a component.

## 8. Browser agent context

Do not send the whole website or resume every turn.

Provide:

- current page/form structure,
- relevant profile fields,
- exact goal.

## 9. Stop conditions

Stop immediately when:

- the task is complete,
- required data is missing,
- the site is unsupported,
- a safety/user approval boundary is reached.

## 10. Development discipline

One task at a time.

After the focused test passes:

```text
update PROGRESS.md
→ commit
→ stop
```

Do not automatically move to the next feature.

## 11. Cost tracking

Record for expensive experiments:

```text
experiment_id
model
input_tokens
output_tokens
cache_read_tokens
cache_creation_tokens
estimated_cost
dataset_version
result
```

`cache_read_tokens` vs. `cache_creation_tokens` tells you directly whether §6's prompt structure is actually working: a high `cache_creation_tokens` count on repeated calls with the same template means something variable is still leaking into the stable prefix.

Use this to identify expensive steps that can be replaced by deterministic logic.
