# Multi-page resume extraction

Improve the existing local PDF reader across varied text-PDF layouts, using the supplied two-page resume as an acceptance case without changing the current user's profile. User approved local extraction + AI only on 2026-10-13; no Google service. AI receives bounded source excerpts only with the existing explicit per-action consent, never PDF bytes. Its Choice API classifies sections; local code selects source-backed facts. Scanned images are not readable by this text-only API.

- Preserve page order, wrapped paragraphs and section boundaries; remove update notes, page footers and icon-only artifacts.
- Extract source-backed name, application email, phone, location, links, education, skills and projects. URL digits must never become a phone number; project paragraphs must not become titles.
- Preserve summary, certifications and achievements as editable profile facts, including facts on page two. Keep account login email separate.
- Cover one-column, sidebar/two-column and multi-page text PDFs with anonymized fixtures. Detect columns from positional section evidence instead of one fixed template; retain uncertain/manual review. Reject image-only or partially unreadable pages before replacing the profile; encrypted, malformed and oversized PDFs retain safe limits. Universal accuracy is not claimed.
- Add nullable profile columns without rewriting existing candidate values. Rollback means restoring the previous application code while retaining added columns/data; destructive production downgrade is outside scope.

History: [shared daily topic](D:/Projects/Sessions/13-10-2026/turio-resume-layouts.md).
