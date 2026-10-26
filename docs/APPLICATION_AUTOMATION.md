# Turio — Application Automation

## Bulk modes — October 14, 2026
The existing request-driven per-application review/approve API is orchestrated
sequentially from the Jobs UI; no submission queue or new engine. Default
fill-and-review prepares answers with per-job previews and manual application
links. Automatic mode's Start action explicitly approves the selected jobs using
current stored profile/resume and confirmed saved answers for that run, then
prepares and submits eligible jobs without a second approval step. Existing
prepared-value approval is also available. Per-job holds, fresh immutable review
tokens and idempotency remain enforced. Run approval lasts 15 minutes; changed,
missing/unconfirmed or unsupported jobs remain pending. Stop finishes only the
current job; uncertain submission outcomes are checked without mutation retries.
Optional batch AI consent sends employer metadata only and resets per action.
Supported fresh hosted transports can submit; other forms retain manual handoff.
Preparation capability is not submission capability. Fixture verification does
not establish company support. Answer once controls group equivalent required
questions; saving updates matching unreviewed owned drafts. Existing reviewed
answers/tokens remain intact until explicit re-preparation loads newer reusable
values. Busy drafts are skipped and can refresh later. Application-only/profile/
AI/file/form-consent answers are not propagated.
ADR-045/047; current evidence: [workflow fixes](evidence/workflow-fixes-2026-10-14.json).

## Stable fields and answer revisions — October 14, 2026

Preparation retains field IDs through metadata upserts; only controls removed by
the employer are retired. Compatible local overrides survive, while current
profile values and AI provenance still follow existing validation. Explicit
preparation refreshes older reusable values from the current saved answer.
Answer batches use an optional expected revision and one atomic commit. UI saves
provide that revision; one harmless stale revision can be refreshed and retried,
but changed edited fields, instructions or AI confidence stop automatic retry and
preserve the user's input. Matching idle unreviewed drafts may receive shared
answers; other reviews stay intact. No migration or duplicate JSONB answer store.
Evidence: [persistence checks](evidence/application-persistence-2026-10-14.json).
The browser engine remains request-driven. Queue/direct ATS/extension transitions
are a later phase; no new ATS coverage or bot-detection guarantee.

## 1. Initial target

The initial Browser Use trial is limited to:
- 1Password
- Linear
- Supabase
- Vercel
- Notion

A company is considered supported only after its actual application workflow is tested end-to-end and evidence is recorded.

## 2. Application adapter

```python
class ApplicationAdapter:
    def can_handle(self, url): ...
    def inspect_form(self, page): ...
    def normalize_field(self, raw_field): ...
    def fill_field(self, field, value): ...
    def upload_resume(self, field, file_ref): ...
    def validate(self, page): ...
```

The exact Python interface may evolve, but website-specific behavior must remain isolated behind the adapter boundary.

## 3. Canonical form schema

The database/API canonical names are:

```json
{
  "field_key": "",
  "label": "",
  "normalized_intent": "",
  "input_type": "",
  "required": true,
  "options": [],
  "source_locator": ""
}
```

The persistent database row id is still the field's `id`/`field_id` reference where required by API payloads.

## 4. Profile-to-form matching

Priority:

```text
exact canonical intent
→ normalized synonym
→ safe semantic match
→ manual/user resolution
```

The mapper must reuse stored information and must not ask the user again for data already present.

Recognized contact labels, including LinkedIn page/link wording, use confirmed
profile facts. Unfamiliar AI-inferred mappings still require explicit confirmation.
Review allows per-field overrides; profile-derived edits default to this application
only. Choosing reuse also synchronizes confirmed canonical contact values to the
profile and advances its version. Local overrides remain scoped to that exact field
when preparing again; other drafts require preparation after profile changes.

Both Jobs and Applications use the shared bulk controls for preparation, matching
question answers and explicit batch approval. Tracker selection preserves each
draft's application ID, even for multiple drafts belonging to the same job.
Uncertain submissions remain locked until the applicant checks the employer site
and confirms no application was submitted. Reset clears approval and requires a
fresh review; it never retries a submission itself.

Each approved form-state RPC remains valid after its exact request has been
accepted, even if a later unrelated POST is blocked. The extra POST never reaches
the employer. Final-submit and original-file-upload permits retain strict
one-use/rejection checks; field values and server receipts still require auditing.

## 5. New information

When a required field cannot be safely populated:

```text
Detect missing field
→ ask user once
→ save answer after confirmation
→ reuse saved answer on later compatible applications
```

## 6. Resume upload

Use the original stored resume file reference. Do not regenerate the resume for an ordinary application submission.

## 7. Sensitive questions

For work authorization, sponsorship, disability, demographic information, or other sensitive data:
- use explicit stored answers only,
- otherwise ask the user,
- never infer from nationality, name, location, education, or resume language.

## 8. Final submission

The agent must stop before final submission until the user explicitly approves the reviewed application.

### Visible browser mode

`BROWSER_HEADLESS` defaults to `true`. Setting it to `false` passes headed mode
to the existing Browser Use runtime. This does not enable automation or alter
domain, resume-integrity, review or submission guards.

Headed mode needs a usable desktop display on the **backend host**. It does not
open the remote user's Chrome, and setting it false in a display-less Docker
container is not a streaming solution. Keep the default in the current Docker
stack. Configuration forwarding/cleanup has unit coverage; a real headed desktop
session and live employer compatibility are not yet verified.

## 9. Failure handling

Show and record:
- stage,
- site/platform,
- failure reason,
- diagnostic id,
- retry availability.

Use bounded retries only.

## 10. Unsupported flow

```text
Stop automation
→ explain unsupported workflow
→ preserve discovered data
→ offer manual continuation
→ track status
```

Never claim an application was submitted when it was not.

## 11. Native-form verification boundary

ADR-033 limits the next verification step to fully intercepted synthetic forms
using the actual browser runtime. Production destinations remain restricted.
Approval must cover the native form destination and values, including original
resume bytes; unrelated requests and duplicate mutation attempts cannot establish
success. JS-only/custom ATS transports remain unsupported until separately audited.
Local fixture evidence is not per-company live support evidence.

The implemented v2 native contract accepts explicit UTF-8 POST forms using
native multipart or URL-encoded bodies. Named hidden fields, multiple inputs and
custom widgets require a separate adapter. Missing optional answers are cleared,
not silently inherited from page defaults. The action/controls are rechecked
around authorization; actual text/file data is checked by a single-use request
permit. Stored resume bytes must also match the upload checksum.

Context page requests are sealed when candidate filling begins; only the approved
matching POST may pass. Service workers/page WebSockets are blocked. Teardown
closes the context/CDP connection, owned browser and driver.

Local result: 130 full-suite passes, including 17 actual-browser fixtures and 14
payload tests. See `evidence/phase6-local-verification-2026-09-15.md`. Arbitrary
JSON transports, pre-submit RPC/uploads, CSRF fields, redirects and live Ashby
pages have not been verified. Do not weaken the guard to make a live page pass.

### Availability before preparation

Application Preparation checks the owner-scoped capability endpoint before
enabling Apply with Agent. Disabled configuration and disallowed URLs are
explained in advance; the employer link/manual tracking remain available.
An available result means the experimental adapter may attempt preparation,
not that the company is validated. The backend still checks eligibility on
every action, and final submission still requires explicit approval.

## Hosted Ashby manual handoff — 2026-10-12

The user's selected workflow is prepare/fill, then user submission. Valid HTTPS
Ashby posting URLs are eligible across company slugs; historical trial tags are
retained only for discovery metadata. Inspection allows pinned public posting and
organization GraphQL queries with exact public-only variables, plus Ashby's asset
CDN. All other mutations remain blocked during inspection. Hosted forms use public
metadata and stable `data-field-path` wrappers, including required/custom fields.

`/review` rechecks a hosted schema without sending candidate values. Explicit
`/handoff` approval binds the current owner, profile, original resume and unexpired
review token. It starts an isolated visible local browser, rechecks the schema,
then releases the reviewed values and original file to the employer page and fills
supported controls. Custom controls, CAPTCHA and final submission remain manual.
The normal employer page can make upload requests after this data-transfer approval;
the agent never clicks its submission button. This is a user-controlled handoff,
not the native adapter's single-use automated submission permit.

The handoff payload travels through stdin and stays in memory; no browser profile
or candidate payload file is persisted. The browser closes on disconnection or after
15 minutes. A successful handoff leaves the application unsubmitted and consumes
the review; only the user can later record manual submission. Hosted schemas are
rejected by `/approve-submit` unless a fresh supported hosted transport is present.
Synthetic browser verification covers original file
bytes and no submit click; live 0x inspection is read-only, not live upload evidence.
History: [shared session](D:/Projects/Sessions/12-10-2026/turio-agent.md).

## Approved hosted submission (2026-10-13)

`ashby-hosted-v2` adds a separately audited form-state transport. After the existing
explicit submission approval, each pinned RPC is bound to fresh form IDs and
reviewed values. S3 upload accepts only the selected owned original PDF and the
employer's bounded upload policy. All stored answers, file identity, field
definitions and omitted defaults are checked before one normal employer submit
action. Only `FormSubmitSuccess` for every application/survey confirms delivery;
HTTP 200 or a button click alone does not. Normal site reCAPTCHA executes unchanged;
challenges are not solved or bypassed. Unknown controls, state changes and uncertain
outcomes stop; submission intent is persisted first and never automatically replayed.

Public 1Password inspection now succeeds for its 37-field form. Required Boolean
questions allow confirmed No, and bounded multiselect arrays preserve chosen
options. Unsupported forms retain the explicit manual handoff above. Old snapshots
must be prepared again. Employer-removed or expired postings leave active job/match
lists without deleting application history; network failures do not count as closure.
Review schemas use `stable-actions-v1`: action titles/definition IDs are stable,
while fresh render/action nonces remain bound by the final submission permit.
Earlier snapshots must be prepared again before automatic eligibility.
Public form reads accept the original query and one exact observed detail-fragment
variant, both bound to the current posting/company-only arguments. Required `Url`
fields use reviewed scalar strings through the same exact-body permits; no URL
fetching or broader GraphQL allowance. Exact 10x public form inspection confirms
six supported required fields; this is inspection evidence, not a live submission.
Evidence: [hosted submission](evidence/hosted-submission-2026-10-13.json).

## Answer reuse and bulk preparation (2026-10-13)

- Preparation reuses profile facts, confirmed answers and missing contact facts available in the selected stored resume. Recognized factual prompts include long labels such as "Please share your LinkedIn profile URL". Sensitive facts are never inferred from resume text.
- Save answers stores confirmed authored values for future applications by default. Contact facts match recognized equivalent labels; custom answers require identical question/control/options. Existing confirmed authored answers and legacy saved keys remain readable. AI suggestions still need explicit confirmation; required form consent remains specific to each application.
- The application form shows missing or unconfirmed values. View filled answers exposes the full summary; Edit saved answers and Edit profile allow corrections before a fresh review.
- Jobs and matches offer bulk selection. Prepare selected applications inspects jobs sequentially; keep the page open. Each result is stored in the application tracker. Failures can be retried, and Stop after current job preserves completed work. Current application state is read before preparation, so existing reviews/submissions are retained.
- Each employer application retains its own final review and explicit handoff/submission approval. Bulk preparation does not perform employer filling or submission.

Shared history: [turio-answer-reuse-bulk.md](D:/Projects/Sessions/13-10-2026/turio-answer-reuse-bulk.md).

### Required-only follow-up (2026-10-13)

- Optional questions are not prompted. Unanswered/unconfirmed optional values neither block review nor enter its answer snapshot. Required suggestions retain confirmation checks.
- Repeated native radio values such as on are represented by unique choice labels. Inspection and filling use the same mapping and reject changed or indistinguishable choices.
- Unanswered optional native fields are disabled, rechecked as exact intended omissions, and excluded from native FormData and SubmissionPermit. Hosted optional controls are skipped without changing their defaults.
- Salary prompts and the filled-answer summary show employer currency/pay-period instructions and an input-format example. Missing currency is explicit; the observed 0g form asks per annum without specifying currency.
- Refresh old drafts with Apply with Agent before creating a new review. Ambiguous historical on values cannot identify a specific choice and need one required selection.

Evidence: [optional-salary-followup-2026-10-13.json](evidence/optional-salary-followup-2026-10-13.json). Shared history remains [turio-answer-reuse-bulk.md](D:/Projects/Sessions/13-10-2026/turio-answer-reuse-bulk.md).
