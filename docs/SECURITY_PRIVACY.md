# Turio — Security and Privacy

## Private verification evidence

Personal-sample reports `jev-live-pilot-2026-10-11.json`, `resume-layouts-2026-10-13.json`
and `resume-heading-spacing-2026-10-13.json` remain private local files, not GitHub
artifacts. Raw QA screenshots, resumes, runtime settings and generated documents
are also excluded. Public documentation retains historical verification counts,
but does not make the underlying private evidence available. Public synthetic and
operational reports are included separately; publication is not new verification
of historical claims or real-employer support.

## 1. Principles

Turio handles resumes, contact information, profile information, and application answers. Treat all user profile information as private application data.

The supplied base-paper material also discusses encryption, access control, MFA, audit logs, transparency, and fairness auditing as relevant security/privacy considerations.

## 2. Storage

- Encrypt data in transit.
- Encrypt sensitive storage where supported.
- Use private object-storage buckets.
- Never expose direct public resume URLs.

## 3. Secrets

Never store secrets in source code.

Use environment variables or a secrets manager.

## 4. Logging

Do not log:
- resume contents,
- full phone/email,
- authentication secrets (passwords, password hashes, raw tokens, token hashes),
- raw sensitive application answers.

Log identifiers and event types instead.

## 5. Access control

Users may access only their own profile/application records.

Enforcement mechanism: JWT access-token middleware attaches `user_id` from the verified token to the request context; every repository query filters by that `user_id`, never by a client-supplied id. See `AUTH.md` for the full token design.

Administrative access must be separately controlled and auditable.

## 6. Browser credentials

Do not store company-site passwords in plaintext.

Do not request credentials unless explicitly required by the supported workflow and a secure credential strategy has been designed.

## 7. Human approval

The user must approve final application submission.

## 8. AI safety

The model must never fabricate:
- experience,
- degrees,
- certifications,
- salary,
- authorization,
- sponsorship status,
- application answers presented as facts.

## 9. Data retention

Define retention policies before production deployment.

## 10. Audit trail

Store application events:

```text
FORM_INSPECTED
FIELD_MAPPED
MISSING_INFO_REQUESTED
ANSWER_CONFIRMED
RESUME_UPLOADED
FORM_VALIDATED
USER_APPROVED
SUBMITTED
SUBMISSION_VERIFIED
FAILED
```


## Retention

Concrete retention periods remain a production-readiness decision. Define and record them before production deployment; do not claim a retention period that has not been approved.

## OpenRouter assistance — 2026-10-13
The user selected free assistance; the fixed model is `dots-studio/dots-3-note-preview:free` instead of the
TypeSafe API. Server code reads only its key aliases in the project-root `.env`;
no key enters browser code, prompts, public evidence or native configuration.
Each action still needs consent; extracted source text may contain personal
information, PDF bytes are not sent and proposals require explicit review/save.

Requests require supported structured parameters and `provider.data_collection`
set to `deny`. OpenRouter's [provider routing guide](https://openrouter.ai/docs/guides/routing/provider-selection)
explains this filter; it is not a blanket account-level zero-retention guarantee.
The [privacy policy](https://openrouter.ai/privacy) states provider practices vary
and users must review their terms. No negotiated DPA/ZDR or deletion deadline is
claimed. Synthetic-only live verification is authorized; no personal PDF transfer
for tests. Unknown chat confidence/probability is null and always review-only;
never simulate Jev's calibrated-looking scores. No TypeSafe or paid model fallback.
ADR-046; historical TypeSafe evidence below remains attributed to that provider.

## Jev assistance: external text transfer

Optional TypeSafe assistance is disabled by default and requires explicit opt-in
for each resume-suggestion or application-preparation action. Resume assistance
sends candidate headings and nearby extracted text, potentially including personal
information, but not PDF bytes. Form mapping sends employer labels, control types
and options; candidate profile values remain local. Consent to assistance never
authorizes an employer submission.

Resume interpretation additionally sends bounded section lines and nearby source
context for company/role/degree/project classification. Contact/legal/preference
fields are not proposed by this path; source contact/legal lines are excluded
from its outbound items. Known source headings stay local. The same explicit
per-action disclosure, retention caveat and accept/versioned-save gates apply.
No PDF bytes, generated values or automatic personal-data transfer (ADR-045).

Bulk automatic mode requires explicit approval of the displayed eligible
application set and values; every submission still carries its own immutable
review token. Changed/expired/held/manual/unconfirmed applications are skipped,
and uncertain submissions are not retried. Choosing a mode or allowing inspection
is not submission consent. Hosted Ashby final submission remains manual.

Source text and employer controls are untrusted data. Sensitive declarations and
consent checkboxes are excluded in code. Model outputs are suggestions requiring
confirmation, not factual or safety guarantees. Logs contain only model/version,
usage, duration and sanitized status; no prompts, credentials or provider bodies.

As of 2026-10-10, live pilot approval and account-specific retention review remain
open. The official legal index is https://docs.typesafe.ai/legal and model data
handling is https://docs.typesafe.ai/models. A no-training statement does not mean
requests are not retained; do not claim zero retention without applicable terms.
Before live testing, record the actual account/DPA terms, retention period,
subprocessors and deletion arrangements here. ADR-041 governs the implementation.

### Synthetic live pilot — 2026-10-11

The user supplied a credential and explicitly authorized live Jev testing and
fixes. The key is retained only in ignored native configuration, not this document
or session history. Initial model listing authenticated successfully. Live
inference uses synthetic resume/form text. The user subsequently selected one
personal PDF and explicitly authorized transfer of selected heading/context excerpts.
Its checks used isolated in-memory profile/storage; no native profile was changed.

Reviewed public [DPA](https://typesafe.ai/legal/data-processing), Schedule I:
retention is purpose/law dependent rather than a fixed number of days. The
[privacy policy](https://typesafe.ai/legal/privacy-policy) allows retention while
reasonably necessary and describes deletion/de-identification requests with legal
exceptions. The [legal index](https://docs.typesafe.ai/legal) offers enterprise ZDR;
this account's enterprise status or negotiated terms are not verified. The linked
trust-center subprocessor list did not expose readable entries to the web tool;
no list or deletion deadline is invented. No zero-retention claim is made.

Personal-data testing requires an identified user-selected resume and the
existing per-action disclosure/consent. No real employer application has been
submitted in verification; browser tests use intercepted fixture pages.

### Approved hosted transport — 2026-10-13

Automatic Start (2026-10-14) explicitly authorizes selected jobs with current
stored profile/resume and confirmed saved answers for one 15-minute run. Missing
answers are not invented; new answers require a new Start action. Each final
submission still requires the existing immutable server review/token, profile
checks and single-use audited transport. Shared-answer updates invalidate pending
reviews and never change busy/terminal or protected application-only answers.

Explicit current individual/batch approval now permits supported hosted employer
RPCs and original-PDF upload. Every transfer rechecks owner, profile, operation
token and current job availability; JSON permits preserve Boolean/number types and
cannot replay. Uploads are bound to original bytes and a verified S3 destination.
After an exact form-state JSON RPC is accepted, a later blocked POST does not
invalidate that accepted RPC. The extra POST still cannot reach the employer;
final submission and original-file upload permits retain strict rejection checks.
The final server form audit rejects changed answers/files, changed definitions,
and newly populated unapproved defaults, including a new implicit No. Normal site
reCAPTCHA is allowed only during approved hosted submission; no challenge bypass.
HTTP 200 alone cannot mark submitted: all forms require FormSubmitSuccess. Failed
or uncertain attempts remain recorded and are never automatically retried.
