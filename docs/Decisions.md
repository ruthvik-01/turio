# Decisions

Canonical decision records live in [[ADR]]. The product-continuation decisions
are ADR-028 through ADR-034. This index avoids duplicating those records.

Source-backed opportunity metadata, operational inventory expansion and resume
preparation maintenance: [[ADR#ADR-037 — Source-backed opportunity metadata and inventory expansion]].

Company suggestions read the existing full discovery catalog rather than distinct
companies from paginated jobs; selection reuses exact canonical-name filtering.
No new company table or schema migration. [[evidence/company-filter-2026-09-16]].

Phase 4 intake: prepare only the unlabeled source-backed pool while awaiting consented candidates; retain the existing seeded sampler and final human-label gates. Local runtime uses the existing attached Compose launcher rather than detached-only startup. [[evidence/phase4-intake-runtime-2026-09-17]].

## Correction: candidate intake is synthetic — September 17, 2026

The user explicitly confirmed all ten supplied profiles are synthetic, not real
consented participants. They are not human ground truth and must not be frozen
or evaluated. Moved candidates.json and draft.json out of active phase4-intake
into ignored experiments/phase4-synthetic-intake, with explicit provenance and
DO NOT FREEZE OR EVALUATE notices. Consent remains false and labels remain empty.
The real source-backed job-pool.json is unchanged. No freeze or evaluation ran.
Phase 4 stays at the human-data boundary; zero eligible human profiles received.
Phase 5 remains on hold under the sequential verification gate.

Synthetic-only Phase 5 functional verification before closing the Phase 4 human gate is explicitly authorized by the user: [[ADR#ADR-038 — Phase 5 synthetic functional verification exception]]. No benchmark freezing/effectiveness evaluation or live-submission permission.

Continue engineering without phase-review pauses, but preserve unmet acceptance gates: [[ADR#ADR-039 — Continue engineering completion without phase-review pauses]].

Browser display configuration, UTF-8 research tooling and measured local optimization without manufactured modalities or labels: [[ADR#ADR-040 — Complete implementable phase tooling without inventing evidence]].

Browser availability UX (September 17): expose the adapter's existing configuration/URL gate through an owner-scoped read endpoint, without opening a browser. Do not enable unvalidated live automation to hide the disabled message. Parser upgrades are opt-in through upload/review, not automatic profile overwrites. See [[evidence/profile-company-usability-2026-09-17]].

Opt-in bounded AI decisions, source-backed review, atomic freshness and retained provenance: [ADR-041](ADR.md#adr-041--opt-in-bounded-ai-assistance). Live requests require separately reviewed retention terms/pilot authorization. The legacy TypeSafe provider and its `JEV_ASSISTANCE.md` document were removed on 2026-10-26; OpenRouter is the only provider.
