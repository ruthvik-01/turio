# Turio — Security and Privacy

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
