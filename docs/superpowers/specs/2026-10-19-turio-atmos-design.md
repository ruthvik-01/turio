# Turio Atmos Redesign

Status: lightweight shared skin implemented; synthetic production UI verification completed 2026-10-20. Source changes remain uncommitted. Native backend/live-employer/research verification remains outside this delivery.

## Goal and evidence

Give Turio the visual feel of [Atmos Gallery](https://atmos.gallery/) while preserving its career-assistance workflows. Apply the design to all 13 existing page routes, not only the landing page.

Public-page accessibility captures, desktop/mobile screenshots, computed styles and the exported nebula renderer informed this design. Atmos uses a WebGL2 volumetric effect as well as CSS fallbacks. The selected Turio treatment is an original CSS/SVG approximation, not a pixel-identical reproduction. Remaining script bodies, image-processing behavior and private backend internals were not fully examined.

Inspection history and canonical REA evidence: [daily topic](../../../../../Projects/Sessions/19-10-2026/turio-atmos-redesign.md). Visual references: [desktop landing](../../../.playwright-mcp/atmos-20261019-011436-home-desktop.png), [desktop workspace](../../../.playwright-mcp/atmos-20261019-011436-create-desktop.png), [mobile dark](../../../.playwright-mcp/atmos-20261019-011436-mobile-dark.png).

## Visual contract

- **Atmosphere:** slow, layered sage, warm-grey and ivory fields around a clear reading area on landing/login/signup. Use CSS gradients/transforms and a small original SVG texture/filter. No WebGL renderer, GSAP, Three.js, Lenis, scroll hijacking or copied reference assets.
- **Shell:** floating, inset pill-shaped header; 24px desktop and 16px mobile gutters. Retain Turio's existing logo, navigation order, active-route indicators and auth/logout actions. Add one accessible light/dark toggle. No sidebar or new routes.
- **Typography:** retain the existing system-sans stack. Use restrained 500–600-weight display text: approximately 40px desktop/28px mobile on the landing hero, 28px/24px page headings, 15px body and at least 16px editable form text. Do not acquire Atmos's commercial font.
- **Materials:** translucent header over decorative backgrounds; mostly opaque workspace surfaces. Thin borders, minimal shadows, pill buttons/tabs and 18–24px content-panel radii. Textareas, long forms and data tables remain practical rather than pill-shaped.
- **Density:** generous landing/auth spacing; quieter, tighter job/application workspaces. Do not put animated fog behind charts, review forms or every data row. Landing footer uses an oversized responsive Turio wordmark; protected pages retain a compact footer.
- **Controls:** at least 44px interactive targets, visible focus, meaningful selected/disabled states and existing input labels. Preserve semantic warning/error/status distinctions, not only decorative colour.

| Role | Light | Dark |
| --- | --- | --- |
| Canvas | `#f5f5f3` | `#141413` |
| Surface | `#fafaf8` | `#1d1d1b` |
| Main text | `#1a1a1a` | `#f4f4ef` |
| Muted text | `#63635b` | `#b6b6ad` |
| Hairline | `#d5d5d0` | `#41413b` |
| Input boundary | `#85857e` | `#939388` |

Primary buttons use main-text colour as their surface and canvas colour for their label. Decorative fields are not allowed to reduce text/control contrast. The existing green logo remains unchanged; neutral treatment replaces the current green-dominant interface styling.

## Theme and motion behaviour

- First visit follows system colour preference. A saved explicit light/dark choice overrides it. Use a validated `turio-theme` browser preference; blocked/empty storage must not break rendering. No server-side preference endpoint or database migration.
- Theme selection must apply to the shell, controls, loading/empty/error states, charts and readable data-table equivalents. Prevent hydration mismatches and avoid flashing the opposite saved theme.
- Use slow transform/opacity motion and brief 150–200ms interaction transitions. Content is visible at rest; no scroll-triggered reveal dependency or continuous JavaScript animation loop.
- Reduced-motion users get a static atmosphere. Reduced-transparency/increased-contrast/forced-colours users get readable solid materials. Unsupported SVG filters fall back to gradients.
- Support every existing Turio workflow at phone width. Do not copy Atmos's desktop-only palette-tool restriction or its narrow-screen redirect.

## Route adaptation and ownership

| Existing routes | Adaptation |
| --- | --- |
| `/`, `/login`, `/signup` | Atmospheric introduction or centred form; existing auth destinations and explanatory content remain truthful. |
| `/home` | Neutral dashboard, existing genuine progress/recommendations/charts; no invented metrics. |
| `/jobs`, `/jobs/[jobId]` | Restyled filters, cards, selection and detail panels; existing pagination and draft actions. |
| `/profile`, `/onboarding` | Clear resume-upload area and grouped profile fields; existing consent, validation and save sequence. |
| `/applications`, `/interviews` | Calm tracker rows/cards and outcome states; Interviews remains the existing filtered tracker. |
| `/applications/[applicationId]`, `/applications/[applicationId]/review` | Clear preparation/review/action hierarchy; required notices and approval checkpoints remain visible. |
| `/resources` | Restrained explanatory panels using existing destinations; no copied Atmos legal or educational content. |

Reuse [globals.css](../../../frontend/app/globals.css), [root layout](../../../frontend/app/layout.tsx) and [shared UI primitives](../../../frontend/components/ui.tsx). Make only necessary presentation changes in the existing screen components and landing/resources pages. Use a shared CSS/SVG decorative layer for landing/auth; it owns neither application data nor routing. Theme preference is isolated from `SessionProvider` and API state.

No changes to API contracts, authentication/proxy behaviour, database schemas, matching methods, upload/storage services or worker logic. Preserve company autocomplete, bulk approval/Stop-after-current, answer revision checks, resume AI consent, reviewed submission, expiry and uncertain-outcome handling. Do not replace the existing staged business changes.

## Verification and acceptance

1. Frontend typecheck (`npm run typecheck -- --incremental false`) and production build pass.
2. All 13 routes render in light and dark at 390, 768 and 1280px without page-level horizontal overflow. Wide tables/navigation may scroll inside their own containers.
3. Keyboard navigation, skip-link visibility, company autocomplete and real pointer interaction with glass navigation retain their existing guarantees.
4. Normal text meets 4.5:1 contrast; large text and meaningful controls meet 3:1. Focus, selections and statuses remain identifiable in both themes and accessibility modes.
5. Theme choice works across navigation/reload, with storage unavailable, and without hydration errors. Reduced motion removes decorative animation.
6. Existing form/review/bulk actions and error/empty/loading states remain intact. Chart values/scales/data-table equivalents are preserved.
7. Update intentional current visual assertions in the existing rendered verifier to this approved contract; do not remove checks to make a redesign pass. Record actual results and screenshots, not historical pass counts.

Before implementation, record the approved direction in `docs/ADR.md`, `docs/FRONTEND.md` and `docs/DESIGN_SYSTEM.md`. Update the project snapshot/progress after verified delivery, with links to shared daily history. Keep all human effectiveness, live-employer and research acceptance gates unchanged.

## Review boundary

Next action: user reviews the implemented UI and [verification results](../../evidence/turio-atmos/results.json). The [execution plan](../plans/2026-10-19-turio-atmos-implementation.md) is completed; native backend/live-device/employer verification remains separate. No commit, deployment, live application submission or paid/external service use is part of this design approval.
