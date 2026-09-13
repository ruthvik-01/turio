# Turio — Dashboard Frontend Specification

## 1. Purpose

This document defines the **Turio logged-in Dashboard screen** shown in the provided visual reference.

The implementation must use this document as the frontend source of truth for this screen.

**Important:** This specification is based on the supplied dashboard image. It does not introduce a new visual direction or redesign.

---

## 2. Screen Identity

- Screen: **Home / Dashboard**
- Product: **Turio**
- User state: Logged-in user
- Primary goal: Give the user an immediate view of career/application progress and the next useful actions.
- Visual character: Premium, calm, minimal, editorial, spacious.
- Main visual language: Soft green/cream environment, white translucent cards, rounded corners, subtle depth, large editorial typography, restrained borders and shadows.

---

# 3. Overall Layout

The dashboard is a desktop-first single-page layout.

### Main regions

1. Global header
2. Hero / progress area
3. Four progress summary cards
4. Applications Over Time chart
5. Application Status chart
6. Recommended for You
7. Today's Focus
8. Motivational quote card

The page uses generous horizontal spacing and avoids a permanent left sidebar.

---

# 4. Global Header

The header spans the full width.

### Left

Turio logo:

- Green Turio symbol
- `Turio` wordmark
- Strong, simple branding
- Positioned with generous left padding

### Navigation

Navigation items:

- Home
- Jobs
- Applications
- Interviews
- Resources

The active item is **Home**.

Active-state treatment:

- Dark text
- Green underline
- Underline positioned close to the label

Inactive navigation:

- Neutral dark text
- No heavy container
- No pill background

### Search

A large rounded search field appears toward the right.

Placeholder:

`Search for jobs, companies or skills...`

Characteristics:

- Search icon
- Soft neutral background
- Rounded corners
- Wide enough for natural search queries

### Right controls

- Notification bell
- Small green notification indicator
- Circular user avatar
- Initial `S`
- Dropdown chevron

---

# 5. Hero / Welcome Section

The hero occupies the first major content area beneath the header.

It is split into two visual areas.

## 5.1 Left content

Small uppercase greeting:

`GOOD TO SEE YOU, SAI`

Large editorial headline:

`Keep going.`

`You’re making progress.`

Supporting copy:

`Find the right opportunities, stay organized, and get closer to the career you want.`

Primary action:

`Browse Jobs →`

Secondary action:

`Update Profile`

### Typography

The headline should be:

- Large
- Editorial/serif-inspired
- High contrast
- Comfortable line height
- Visually dominant

The supporting text should be considerably smaller and calmer.

---

# 6. Hero Visual / Quote Area

The right side contains a large rounded visual panel.

It uses a soft nature-inspired image/abstract background with:

- Green foliage
- Soft cream tones
- Subtle blurred background
- Large rounded corners

Inside the visual are translucent/frosted quote cards.

### Quote 1

`Progress takes consistency, not perfection.`

A short horizontal divider appears beneath it.

### Quote 2

`A brighter tomorrow is a series of small steps.`

A short horizontal divider appears beneath it.

The quote cards should feel integrated into the hero rather than looking like ordinary dashboard widgets.

---

# 7. Progress Summary Cards

Immediately below the hero are four large cards.

They form one horizontal row on desktop.

## Card 1 — Applications

Icon:

- Document/application icon

Value:

`12`

Label:

`Applications`

Right side:

- Chevron

---

## Card 2 — Interviews

Icon:

- People/group icon

Value:

`8`

Label:

`Interviews`

Right side:

- Chevron

---

## Card 3 — Offers

Icon:

- Briefcase icon

Value:

`3`

Label:

`Offers`

Right side:

- Chevron

---

## Card 4 — In Progress

Icon:

- Clock icon

Value:

`5`

Label:

`In Progress`

Right side:

- Chevron

---

## Card styling

Cards should:

- Have rounded corners
- Use a light/white surface
- Have subtle depth
- Use soft green/cream icon backgrounds
- Maintain generous internal padding
- Keep numbers visually prominent
- Keep labels simple
- Avoid excessive decoration

---

# 8. Applications Over Time

This is the main analytical card on the left.

Title:

`Applications Over Time`

Top-right control:

`Last 4 weeks` + dropdown chevron

### Chart

A clean bar chart displays application activity over time.

Visible x-axis labels include:

- Aug 15
- Aug 22
- Aug 29
- Sep 5
- Sep 12

The bars use a muted green visual treatment.

### Chart principles

- Minimal grid
- No unnecessary chart decoration
- Clear axis labels
- Soft visual weight
- Rounded bar tops where supported
- Maintain enough whitespace around the chart

---

# 9. Application Status

This card sits to the right of Applications Over Time.

Title:

`Application Status`

### Donut chart

Center:

`12`

`Total`

Status categories:

| Status | Count |
|---|---:|
| Applied | 4 |
| Under Review | 5 |
| Interview | 2 |
| Rejected | 1 |

### Legend

Each status has:

- Small circular indicator
- Status name
- Count aligned to the right

The status visualization should remain simple and readable.

---

# 10. Recommended for You

A wide card appears below the analytical cards.

Header:

`Recommended for You`

Right-side action:

`View all →`

### Recommendation cards

The section contains job recommendation cards.

Example entries shown in the reference:

#### Google

- Role: Software Engineer
- Company: Google
- Location: Bangalore, India
- Employment: Full-time

#### Notion

- Role: Product Analyst
- Company: Notion
- Location: Remote
- Employment: Full-time

#### Microsoft

- Role: Frontend Engineer
- Company: Microsoft
- Location: Hyderabad, India
- Employment: Full-time

Each card includes:

- Company logo
- Job title
- Company name
- Location
- Employment type
- Bookmark action

Cards should remain compact and scannable.

---

# 11. Today's Focus

A separate card sits beside Recommended for You.

Header:

`Today’s Focus`

Right-side action:

`View all →`

Checklist items:

1. `Complete application for Google`
2. `Prepare for interview (Notion)`
3. `Update resume`
4. `Explore 5 new opportunities`

### Completed state

The first item is shown as completed:

- Green circular check
- Text appears crossed out/subdued

### Pending state

Pending items use:

- Empty circular checkbox
- Normal dark text

The checklist should feel lightweight rather than like a large project-management interface.

---

# 12. Motivational Quote Card

A small card appears beside Today's Focus.

Visual:

- Small circular leaf icon
- Quote text
- Small divider

Quote:

`Every rejection is a step closer to the right fit.`

The card is intentionally simple.

Its purpose is to add emotional warmth without becoming distracting.

---

# 13. Visual Design System

## Color direction

Use the visual reference as the source of truth.

Primary visual family:

- Deep charcoal/navy text
- Soft cream background
- White/off-white surfaces
- Muted natural greens
- Very subtle pale gold accents
- Soft translucent effects

Avoid:

- Highly saturated colors
- Neon gradients
- Dark dashboard themes
- Excessive colored cards
- Strong shadows

---

# 14. Glass / Frosted Surfaces

The reference uses a soft glass-like treatment.

Use it carefully.

### Characteristics

- Semi-transparent light surface
- Background blur where appropriate
- Thin low-contrast border
- Very soft shadow
- Rounded corners

Glass should support the visual hierarchy rather than cover the whole page.

Do **not** turn every component into heavy glassmorphism.

---

# 15. Corner Radius

Use consistently rounded surfaces.

Recommended hierarchy:

- Large hero panel: large radius
- Main cards: medium-large radius
- Buttons: pill/rounded
- Search: rounded
- Small controls: rounded

Avoid sharp rectangular containers unless required for a specific control.

---

# 16. Typography

The typography should reproduce the contrast visible in the reference.

### Display typography

Used for:

- Hero headline
- Major editorial statements

Characteristics:

- Large
- Elegant
- Serif/editorial feel

### UI typography

Used for:

- Navigation
- Buttons
- Labels
- Job information
- Chart labels

Characteristics:

- Clean sans-serif
- Excellent readability
- Medium/semibold hierarchy

Do not use decorative fonts for ordinary interface text.

---

# 17. Spacing

The interface should breathe.

Prioritize:

- Large outer page margins
- Generous hero spacing
- Comfortable card padding
- Clear separation between dashboard sections
- Consistent vertical rhythm

Do not compress the dashboard just to fit more information.

---

# 18. Responsive Behavior

## Desktop

Maintain the composition shown in the reference.

- Full navigation
- Wide hero
- Four summary cards in a row
- Two-column analytics
- Multi-card recommendation area

## Tablet

- Reduce horizontal spacing
- Keep navigation usable
- Allow summary cards to wrap
- Keep charts readable
- Reduce hero visual size if necessary

## Mobile

Do not use a permanent desktop sidebar.

Use a compact mobile navigation pattern.

The layout should become a vertical content flow:

1. Header
2. Greeting
3. Hero visual
4. Progress cards
5. Applications chart
6. Status chart
7. Recommendations
8. Today's Focus
9. Quote

Cards should become full-width or two-column where space permits.

---

# 19. Interaction Principles

Animations should be subtle.

Use motion for:

- Navigation state changes
- Card hover
- Button hover
- Chart appearance
- Checklist completion
- Search focus
- Page transitions

Animation should feel smooth and premium.

Avoid:

- Bouncy animations
- Excessive scaling
- Large parallax effects
- Constant movement
- Distracting background animation

---

# 20. Functional Meaning

The dashboard is not only visual.

Each major element should lead to a useful action.

### Progress cards

- Applications → application tracking
- Interviews → interview tracking
- Offers → offer tracking
- In Progress → active applications/tasks

### Hero actions

- Browse Jobs → job discovery
- Update Profile → profile/resume information

### Recommended jobs

Selecting a recommendation opens its job details/application flow.

### Today's Focus

Selecting an item opens the relevant workflow.

### Header navigation

- Home → dashboard
- Jobs → job discovery
- Applications → application tracking
- Interviews → interview management
- Resources → career resources

---

# 21. Data Requirements

The dashboard should consume real application/profile data rather than hard-coded values in production.

Required dashboard data includes:

- User name
- Application count
- Interview count
- Offer count
- Active/in-progress count
- Application history
- Application status distribution
- Recommended jobs
- Today's focus tasks
- User avatar/initial

The values visible in the supplied image are visual-reference examples.

---

# 22. Component Structure

Suggested frontend component hierarchy:

```text
Dashboard
├── Header
│   ├── Logo
│   ├── Navigation
│   ├── Search
│   ├── Notifications
│   └── UserMenu
│
├── Hero
│   ├── WelcomeCopy
│   ├── PrimaryActions
│   └── ProgressQuoteVisual
│
├── ProgressSummary
│   ├── ApplicationsCard
│   ├── InterviewsCard
│   ├── OffersCard
│   └── InProgressCard
│
├── Analytics
│   ├── ApplicationsOverTime
│   └── ApplicationStatus
│
├── LowerContent
│   ├── RecommendedForYou
│   ├── TodaysFocus
│   └── MotivationCard
│
└── ResponsiveNavigation
```

---

# 23. Important Frontend Rule

**Do not invent additional dashboard panels simply to fill empty space.**

Every visible element should have a clear purpose.

The target feeling is:

> **calm, premium, focused, and useful.**

The dashboard should feel closer to a polished consumer product than a conventional enterprise admin dashboard.

---

# 24. Visual Reference

The supplied dashboard image is the visual reference for this specification.

The implementation should reproduce its:

- Layout hierarchy
- Content density
- Typography contrast
- Rounded surfaces
- Green/cream visual language
- Hero composition
- Analytics structure
- Recommendation structure
- Focus checklist
- Motivational content

This document describes the reference; it should not be interpreted as permission to introduce a different visual direction.
