# Turio — Frontend Specification (Authoritative)

## 0. Purpose and source-of-truth status

This is the **single authoritative frontend specification** for Turio.

It defines:
- frontend architecture,
- screen inventory,
- UI states,
- component families,
- dynamic application UI,
- accessibility/performance requirements,
- and the currently approved visual direction.

`DESIGN_SYSTEM.md` is a supporting token/reference file only. It must not define a competing layout, navigation model, typography system, or visual direction.

`DESIGN_REFERENCE_SOURCE.md` is a raw reference archive and is not an authority for new UI decisions.

**Frontend freeze rule:** Do not introduce new frontend concepts, navigation patterns, layouts, animations, components, colors, or visual directions unless the user explicitly requests the change and the decision is recorded in `ADR.md` before implementation.

## 1. Product principle

The UI should hide agent complexity and surface only the next meaningful user decision.

Core experience:

```text
Find → Match → Apply → Review → Track
```

The interface should feel premium, calm, spacious, clear, and consumer-product oriented rather than like a dense enterprise admin dashboard.

## 2. Current approved visual direction

ADR-049 records the user's correction (2026-10-20): centered text-only Turio branding on public pages, no duplicated header auth controls, a real volumetric WebGL field with static fallback, and measured hover/exit/surface/heading/content transitions matching the reference's motion language. The prior CSS-gradient delivery was rejected; synthetic style checks alone are not visual acceptance or real-login evidence.

The approved direction includes:
- near-white/charcoal light and dark canvases with opaque workspace surfaces,
- a text-only Turio name, centered on public pages, with no copied reference branding,
- an inset pill-shaped frosted top header and pill actions/tabs,
- 500–600-weight system-sans display and UI text,
- generous public-page spacing and practical data/form layouts,
- no permanent desktop left sidebar or new routes,
- existing navigation/auth actions and responsive mobile workflows,
- original volumetric WebGL field plus measured route, hover and staggered reveal motion,
- static/solid accessibility fallbacks, no new animation package, commercial font or copied reference asset.

Detailed contract: [Turio Atmos design](superpowers/specs/2026-10-19-turio-atmos-design.md).

Do not turn the whole interface into heavy glassmorphism. Glass is a supporting material, not the entire UI.

## 3. Typography

### Display

Use the existing system-sans family for hero and page headings, with 500–600 weight and restrained scale. Landing headings use 40px desktop/28px mobile; page headings use 28px/24px. Do not add serif headings or marketing filler.

### UI

Use Inter/system sans-serif for:
- navigation,
- buttons,
- labels,
- forms,
- job metadata,
- tables,
- charts.

### Brand

The Turio logo/wordmark is an asset. Do not recreate the wordmark using a web font.

## 4. Shape and elevation

- Large cards/panels: generous rounded corners.
- Buttons: rounded/pill where appropriate.
- Inputs: rounded and clear.
- Glass surfaces: thin low-contrast border + soft blur + restrained shadow.
- No heavy shadows on every element.
- No sharp/square styling unless a native control requires it.

## 5. Color direction

Use paired near-white/charcoal palettes from the approved design spec. Primary interface actions are neutral; the supplied green logo remains unchanged. Existing status/chart roles retain labels and non-colour encodings, with readable themed surfaces.

Supporting neutrals:
- strong light/dark text and readable muted metadata,
- mostly opaque workspace/input surfaces,
- thin decorative hairlines and stronger input boundaries,
- restrained success/warning/danger colours only where status semantics require them.

Do not introduce competing bright accent colors merely for decoration.

Exact implementation tokens live in `DESIGN_SYSTEM.md`.

## 6. Desktop navigation

Use a horizontal top navigation rather than a permanent left sidebar.

Reference navigation:

```text
Turio | Home | Jobs | Applications | Interviews | Resources | Search | Notifications | Profile
```

The current reference does not require a desktop sidebar.

## 7. Core screen inventory

### 7.1 Marketing / landing

Purpose: explain Turio and start onboarding.

Core elements:
- brand/header,
- hero statement,
- concise product explanation,
- primary CTA,
- secondary CTA,
- trust/social-proof area,
- restrained decorative visual.

### 7.2 Onboarding — personal information

Collect only information needed to establish the initial profile.

### 7.3 Onboarding — skills

Searchable multi-select skill input with selected-state chips.

### 7.4 Onboarding — resume upload

Resume upload/drop area followed by extraction progress and profile review.

The original uploaded file remains the stored source artifact.

### 7.5 Home / dashboard

The approved dashboard reference contains:
- top navigation,
- personalized greeting,
- hero/progress visual,
- four progress summary cards,
- Applications Over Time chart,
- Application Status donut chart,
- Recommended for You,
- Today's Focus,
- motivational quote card.

The exact dashboard content and hierarchy are specified in `Turio_Dashboard_Frontend.md` when that file is present in the working docs set.

### 7.6 Job discovery

Purpose: scan and compare recommendations.

Show:
- search,
- filters,
- ranked jobs,
- match score,
- matched skills,
- compact metadata.

### 7.7 Job detail

Purpose: make the decision to apply.

Show only meaningful supporting context:
- company,
- title,
- location,
- employment type,
- salary if available,
- requirements,
- match score,
- evidence/explanation,
- Apply action.

### 7.8 Application assistant

Purpose: show progress while the system prepares a supported application.

Show:
- current step,
- completed/pending state,
- detected field summary,
- browser/application preview when appropriate,
- elapsed time/status,
- Stop action.

### 7.9 Missing information

Show **only genuinely missing required information**.

Known database values must not be re-requested.

Example:

```text
4 fields already known
2 fields missing
1 written question
```

The UI should ask only for the 2 missing fields.

### 7.10 AI answer review

For open-ended application questions:
- show the question,
- show the generated draft,
- allow editing,
- show that the answer is a draft,
- require user confirmation before use.

### 7.11 Final review

Purpose: final human checkpoint before submission.

Show:
- prepared application fields,
- prepared answers,
- resume being used,
- editable controls,
- clear final submission action.

The page must clearly communicate that submission has not yet occurred.

### 7.12 Application tracking

Show:
- status filters/tabs,
- application rows/cards,
- company,
- role,
- status,
- submitted date,
- outcome when known,
- next useful action.

This is allowed to be denser than decision screens because the user is scanning a collection.

### 7.13 Analytics

Show concise aggregate metrics and one or a small number of purposeful visualizations. Avoid dashboard clutter.

### 7.14 Mobile

Use a compact mobile navigation model appropriate to the existing approved reference. Do not introduce a new navigation pattern without explicit approval.

## 8. UI state model

```text
idle
loading
ready
needs_input
review
success
error
```

The state must be visible through text, icons, structure, or accessible status semantics — not color alone.

## 9. Component families

- Header/navigation
- Hero
- Search
- Job card
- Match score
- Evidence list
- Profile field
- Missing-field prompt
- Stepper/progress indicator
- Application assistant status panel
- Browser preview panel
- Review panel
- Tracking row/card
- Stat card
- Chart
- Toast/status message
- Modal only when necessary

## 10. Dynamic application UI

Application forms are dynamic. The frontend must render from the normalized form schema returned by the backend.

The frontend must not hard-code assumptions about every company's application fields.

The backend decides:
- what field was detected,
- whether it is required,
- what normalized intent it has,
- whether a value already exists,
- whether user input is required.

The frontend presents that result clearly.

## 11. Accessibility

- Keyboard accessible.
- Visible focus states.
- Every form control has a label.
- Sufficient contrast.
- Error text appears next to the relevant control.
- Do not encode meaning by color alone.
- Maintain touch targets of at least 44px where applicable.

## 12. Performance

- Server-render static/low-change content where useful.
- Cache jobs/recommendations.
- Lazy-load expensive agent views.
- Prefer event-driven updates over continuous polling when possible.
- Do not re-render large lists unnecessarily.

## 13. Frontend/backend boundary

The frontend must never contain:
- database credentials,
- Browser Use credentials,
- secret API keys,
- hidden production ranking weights,
- privileged application-submission logic.

All protected operations go through backend APIs.

## 14. Form implementation rules

Every meaningful form must specify:
- purpose,
- fields,
- validation,
- loading state,
- empty state where relevant,
- error state,
- success state,
- disabled state,
- submit/cancel behavior,
- accessibility labels,
- backend endpoint used.

Do not create a visual-only form that has no defined data contract.

## 15. Route ownership

Frontend route paths are defined centrally in `API_SPEC.md` for backend calls and should be implemented as a coherent App Router structure. Suggested page routes:

```text
/
/onboarding
/home
/jobs
/jobs/[jobId]
/applications
/applications/[applicationId]
/applications/[applicationId]/review
/interviews
/resources
/analytics
/profile
```

These are page-level navigation paths, not API endpoints. Do not add routes solely for cosmetic purposes.

## 16. Do / Don't

### Do
- preserve whitespace,
- keep hierarchy obvious,
- use subtle glass only where it helps,
- keep one primary action per decision screen,
- make automation status understandable,
- use original brand assets,
- keep forms calm and readable.

### Don't
- add a permanent desktop sidebar,
- create a dense admin-style dashboard,
- use decorative gradients as functional UI,
- ask for information already stored in the profile database,
- hide submission boundaries,
- use AI-generated filler content to occupy empty space,
- introduce new visual directions without explicit approval.
