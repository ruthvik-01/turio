# Turio — Token Budget and Cost Control

## 1. Goal

The project is being developed under a very small external-model budget.
(like 1 dollar of deepseek) Optimize for **useful work per token**, not maximum model usage.

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

## 6. Structured outputs

Prefer JSON/schema outputs over long prose when the model is acting as a component.

## 7. Browser agent context

Do not send the whole website or resume every turn.

Provide:

- current page/form structure,
- relevant profile fields,
- exact goal.

## 8. Stop conditions

Stop immediately when:

- the task is complete,
- required data is missing,
- the site is unsupported,
- a safety/user approval boundary is reached.

## 9. Development discipline

One task at a time.

After the focused test passes:

```text
update PROGRESS.md
→ commit
→ stop
```

Do not automatically move to the next feature.

## 10. Cost tracking

Record for expensive experiments:

```text
experiment_id
model
input_tokens
output_tokens
estimated_cost
dataset_version
result
```

Use this to identify expensive steps that can be replaced by deterministic logic.
