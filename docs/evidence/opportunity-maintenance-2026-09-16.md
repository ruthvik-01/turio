# Opportunity maintenance — September 16, 2026

## Outcome

Implemented the requested maintenance within the existing FastAPI/service/repository,
Next.js and Browser Use/native-adapter architecture. Existing uncommitted work was
preserved. Phase 4 remains active; Phase 5 was not started.

- **Eligibility:** nullable source-backed deadlines; expired jobs excluded before
  pagination/counting and matching. Eligible-inventory fingerprints invalidate
  cached recommendations as time passes. Expired detail returns 404; application
  creation/preparation is rejected. Unknown deadlines retain existing behavior.
- **Description:** deterministic readable presentation of the actual stored text;
  HTML/Markdown emphasis and decorative asterisks are cleaned without generated
  copy, summaries or fabricated requirements. Stored matching text is unchanged.
- **Agent:** Application Preparation now has Apply with Agent, calling the existing
  `/start` endpoint. Review and explicit approve-submit remain separate. Disabled
  or unsupported automation still fails visibly and safely.
- **Resume:** valid PDFs with generic/empty browser MIME can pass signature/parser
  checks; invalid data remains rejected. Drafts created before the first resume
  upload attach the stored resume on preparation. Recognized resume/CV labels map
  to the original stored document. Existing selections are not silently replaced.
- **Logo:** sourced HTTPS images replace company-initial placeholders at existing
  dimensions. Unavailable/failed images use a neutral company symbol, not fake branding.
- **Inventory:** checksum-verified Stapply Ashby feeds produce a 3,448-company
  discovery catalog and a separate operational union. The original Phase 4 CSV
  is untouched. All five trials remain; every catalog entry is explicitly
  automation-unvalidated. No browser allowlist or new ATS adapter was added.

## Deployment and data

The existing local Compose verification stack was rebuilt (backend, worker,
frontend); PostgreSQL migration `a230916001` ran successfully. Its existing ignored
environment file now selects `data/stapply-expanded-jobs.csv`.

Import: **56,344 rows read; 1,150 inserted; 55,189 updated; five rejected**.
Final database: **56,339 jobs**, 2,883 distinct canonical company names (2,917
source company slugs in the catalog have jobs), **290 jobs with sourced logos**.
The catalog itself includes 3,448 discovery candidates, not 3,448 validated employers.
The feed has **zero reliable deadlines**; none were fabricated or derived from
posting dates. Unknown-deadline jobs therefore remain visible.

Sources, checksums, counts, migration and PostgreSQL probe evidence:
[[stapply-expansion-2026-09-16]]. Logo provenance:
[[company-logo-sources-2026-09-16]].

## Verification

| Check | Result |
|---|---|
| Focused jobs/resume/application/native-browser/Phase 4 backend selection | 111 passed in 119.91s |
| Final full backend run, native-browser and offline-model flags enabled | 179 passed, one known failure in 122.06s |
| Full-run failure | Existing `test_unchanged_import_keeps_heartbeat_responsive`: artificial 0.4s lease becomes interrupted |
| Frontend typecheck | Passed |
| Frontend production build and Compose image rebuild | Passed |
| PostgreSQL additive migration | Passed |
| Self-cleaning PostgreSQL normalization/update/no-op/expired-job predicate probe | Passed |
| Deployed browser checks | Eight check groups passed; zero uncaught page errors |
| Submission behavior | Zero employer submissions; explicit approval boundary preserved |
| Final whitespace check | Passed |

The deployed browser checks exercise signup, generic-MIME PDF upload through the
real proxy/API/PostgreSQL/MinIO path, original resume reuse in application
preparation, source-backed 0x logo loading, description DOM rendering, disabled-agent
error handling, 390px layout and logout. Final-review UI actions are explicitly
intercepted fixtures, not live agent success. Separate native-browser integration
tests traverse the real application API and verify exact original resume bytes in
the target form/multipart request, no pre-approval POST and one approved submission.
These native tests are entirely intercepted employer fixtures, not company validation.
Screenshots were captured; automated DOM/image-load/layout assertions passed.

The first deployed-logo attempt ran before the inventory transaction committed
and correctly found no logo; the complete post-import rerun passed. Browser
results: [[opportunity-ui-2026-09-16/results]].

## Remaining limits

- The already-recorded short-lease worker-heartbeat failure was not changed.
- Browser automation remains disabled by default; no employer workflow is live-validated.
- Logos exist only where observed source data is available; missing images remain neutral.
- Unknown deadlines are not evidence that a posting is still accepting applications.
- Phase 4 effectiveness results still require consented, independently human-annotated
  data. No labels, scores, success rates or support claims were manufactured.
- Obsidian MCP resources were unavailable. Repository documentation and the requested
  local memory index were updated; no Obsidian synchronization is claimed.

## Files changed in this request

This list excludes pre-existing unrelated working-tree changes. Local downloaded
CSVs/catalogs and runtime logs remain ignored; the existing stack environment
received only the dataset-path setting described above.

- `D:/College/4-2 project/alembic/versions/a230916001_job_metadata.py`
- `D:/College/4-2 project/backend/app/models/job.py`
- `D:/College/4-2 project/backend/app/schemas/job.py`
- `D:/College/4-2 project/backend/app/repositories/jobs.py`
- `D:/College/4-2 project/backend/app/services/job_metadata.py`
- `D:/College/4-2 project/backend/app/services/job_normalize.py`
- `D:/College/4-2 project/backend/app/services/job_ingestion.py`
- `D:/College/4-2 project/backend/app/services/jobs.py`
- `D:/College/4-2 project/backend/app/services/applications.py`
- `D:/College/4-2 project/backend/app/services/form_mapping.py`
- `D:/College/4-2 project/backend/app/services/resume_pipeline.py`
- `D:/College/4-2 project/frontend/lib/types.ts`
- `D:/College/4-2 project/frontend/components/ui.tsx`
- `D:/College/4-2 project/frontend/components/applications.tsx`
- `D:/College/4-2 project/frontend/components/profile.tsx`
- `D:/College/4-2 project/backend/tests/test_job_presentation.py`
- `D:/College/4-2 project/backend/tests/test_company_inventory.py`
- `D:/College/4-2 project/backend/tests/test_applications.py`
- `D:/College/4-2 project/backend/tests/test_browser_adapter.py`
- `D:/College/4-2 project/backend/tests/test_resumes.py`
- `D:/College/4-2 project/scripts/prepare_company_inventory.py`
- `D:/College/4-2 project/scripts/verify_job_updates.py`
- `D:/College/4-2 project/scripts/verify_opportunity_ui.py`
- `D:/College/4-2 project/scripts/smoke_ui.py`
- `D:/College/4-2 project/docs/ADR.md`
- `D:/College/4-2 project/docs/API_SPEC.md`
- `D:/College/4-2 project/docs/APIs.md`
- `D:/College/4-2 project/docs/DATABASE.md`
- `D:/College/4-2 project/docs/DEPLOYMENT.md`
- `D:/College/4-2 project/docs/Architecture.md`
- `D:/College/4-2 project/docs/SUPPORTED_COMPANIES.md`
- `D:/College/4-2 project/docs/Decisions.md`
- `D:/College/4-2 project/docs/PROJECT_CONTEXT.md`
- `D:/College/4-2 project/docs/PROGRESS.md`
- `D:/College/4-2 project/docs/Bugs.md`
- `D:/College/4-2 project/docs/TODO.md`
- `D:/College/4-2 project/docs/Changelog.md`
- `D:/College/4-2 project/docs/Sessions/2026-09-16.md`
- `D:/College/4-2 project/docs/evidence/company-logo-sources-2026-09-16.json`
- `D:/College/4-2 project/docs/evidence/stapply-expansion-2026-09-16.json`
- `D:/College/4-2 project/docs/evidence/opportunity-ui-2026-09-16/results.json`
- `D:/College/4-2 project/docs/evidence/opportunity-ui-2026-09-16/job-detail.png`
- `D:/College/4-2 project/docs/evidence/opportunity-ui-2026-09-16/application-preparation.png`
