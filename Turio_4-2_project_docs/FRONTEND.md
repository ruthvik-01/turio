# Turio — Frontend Architecture

## 1. Product principle

The UI should hide agent complexity and surface only the next meaningful user decision.

Core experience:

```text
Find
→ Match
→ Apply
→ Review
→ Track
```

The interface should feel premium, restrained, spacious, and editorial rather than like a dense admin dashboard.

## 2. Planned stack

- Next.js
- React
- TypeScript
- Tailwind CSS
- CSS variables
- Accessible semantic HTML
- Lightweight icon library or inline line icons

## 3. Main screens

### Onboarding / Resume
Upload resume once and review extracted profile.

### Home
- recommended roles,
- current application progress,
- recent activity.

### Job discovery
Search/filter/ranked jobs.

### Job detail
- company,
- title,
- location,
- requirements,
- match score,
- explanation,
- Apply action.

### Application assistant
Shows application preparation state.

### Missing information
Shows only fields not already available.

### AI answer review
Shows generated draft and editing area.

### Final review
Shows all information before submission.

### Tracker
Shows submitted/application states.

## 4. UI state model

```text
idle
loading
ready
needs_input
review
success
error
```

## 5. Component families

- Navigation
- Hero
- Job card
- Match score
- Evidence list
- Profile field
- Missing-field prompt
- Application stepper
- Browser activity panel
- Review panel
- Tracker row
- Toast/status
- Modal only when necessary

## 6. Avoid dense dashboards

Do not put every workflow into one screen.

Prefer:

```text
one primary task
+
small amount of supporting context
+
one strong primary action
```

## 7. Dynamic application UI

The UI should adapt to the actual form schema.

Example:

```text
4 fields already known
2 fields missing
1 written question
```

Then show:

> Everything is ready except 2 details.

Ask for those details only.

## 8. Accessibility

- keyboard accessible,
- visible focus states,
- labels for every form control,
- sufficient contrast,
- error text adjacent to the relevant control,
- do not encode meaning by color alone.

## 9. Performance

- server-render static/low-change content,
- cache jobs/recommendations,
- lazy load expensive agent views,
- avoid continuous polling when event-driven updates work.

## 10. Frontend-backend boundary

Frontend never contains:
- matching weights as hidden business logic,
- database credentials,
- Browser Use credentials,
- secret API keys.

Use backend APIs for all protected operations.
