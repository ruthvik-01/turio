
# Soft UI Design Guide

A practical guide to building a **soft UI** interface, based on the style in your reference screenshots (warm beige palette, serif + sans pairing, big rounded cards, diffused shadows) and on published design and accessibility references.

---

## 1. What it is

**Soft UI** is a visual style where interface elements feel gentle, light and slightly tactile. It uses low-contrast muted colors, rounded shapes, and soft shadows instead of hard borders or flat color blocks.

It is closely related to **neumorphism** ("new skeuomorphism"), a term coined by Jason Kelly. Neumorphism sits between skeuomorphism (imitating real objects) and flat design (no depth). Wikipedia notes that neumorphism is also called soft UI, and that it became widely known after concept shots on Dribbble and after Apple's macOS Big Sur (2020) used similar soft icons and translucency.

### Two flavors (important distinction)

|               | Strict neumorphism                                                    | Modern soft UI (your screenshots)            |
| ------------- | --------------------------------------------------------------------- | -------------------------------------------- |
| Surface color | Element = same color as background                                    | Cards are lighter than the background        |
| Depth         | Dual shadow (light + dark) makes elements look extruded or pressed in | One diffused shadow makes cards float        |
| Contrast      | Very low                                                              | Low, but text and controls are kept readable |
| Accessibility | Often poor                                                            | Much easier to make compliant                |

> My assessment: your screenshots are the second flavor. It is the one used in real products, because strict neumorphism has known accessibility problems (see section 8).

---

## 2. Why it is used

- **Calm, premium feel.** Good for wellness, meditation, journaling, finance-lite and community apps.
- **Brand differentiation.** A distinctive look compared to the default Material or flat styles.
- **Approachability.** Rounded shapes and warm tones feel friendly.

**Trade-off:** it maximizes calm at a cost to clarity. Several design references recommend using it as an accent or as a calm single-purpose-screen style, not as a whole system for dense, data-heavy products.

---

## 3. Core principles

1. **Muted, low-saturation palette.** Warm neutrals plus exactly **one** accent color.
2. **Large radii.** Cards 20-28px, pills fully rounded.
3. **Soft, diffused shadows.** Large blur, low opacity, warm-tinted (never pure black).
4. **Layered surfaces.** Background, then surface, then card. Depth comes from tone steps, not borders.
5. **Typography does the hierarchy.** Serif for headings and emotional content, clean sans for UI.
6. **Generous whitespace.** Padding of 16-24px, breathing room between cards.
7. **Thin line icons.** 1.5px stroke, consistent set.
8. **Readable where it matters.** Soft everywhere except text, controls and focus states.

---

## 4. Design tokens

Start every soft UI project with tokens. Contrast ratios below were calculated with the WCAG formula.

```css
:root {
  /* Colors */
  --bg:           #D9C8C0;
  --surface:      #F5F1EC;
  --card:         #FFFFFF;
  --text:         #2B2623;
  --text-muted:   #6B625C;
  --border-ui:    #8C7F77;
  --accent:       #9B2C2C;
  --accent-soft:  #F3DEDE;

  /* Radius */
  --radius-sm:    12px;
  --radius-md:    20px;
  --radius-lg:    28px;
  --radius-pill:  999px;

  /* Shadows */
  --shadow-card:  0 8px 24px rgba(80, 50, 40, 0.10);
  --shadow-float: 0 16px 40px rgba(80, 50, 40, 0.14);
  --shadow-press: inset 0 2px 6px rgba(80, 50, 40, 0.12);

  /* Spacing (4px scale) */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;

  /* Type */
  --font-serif: "EB Garamond", "Cormorant Garamond", Georgia, serif;
  --font-sans:  "Inter", "Plus Jakarta Sans", system-ui, sans-serif;
}
```

### Verified contrast of this palette

| Pair | Ratio | Needed (WCAG AA) | Result |
| ---------------------------------- | ------- | ------------------- | -------------------------------- |
| `--text` on `--card` | 14.95:1 | 4.5:1 | Pass |
| `--text` on `--surface` | 13.30:1 | 4.5:1 | Pass |
| `--text-muted` on `--card` | 5.95:1 | 4.5:1 | Pass |
| `--text-muted` on `--surface` | 5.30:1 | 4.5:1 | Pass |
| `--accent` on `--card` | 7.53:1 | 4.5:1 | Pass |
| White text on `--accent` | 7.53:1 | 4.5:1 | Pass |
| `--border-ui` on `--card` | 3.88:1 | 3:1 (UI components) | Pass |
| `--card` vs `--bg` (no border) | 1.62:1 | n/a, decorative | Fine for cards, not for controls |

> **Correction to my earlier message:** I suggested `#8A817B` for muted text. On white it measures 3.81:1, which fails the 4.5:1 text requirement. Use `#6B625C` instead.

---

## 5. Component recipes

### Card

```css
.card {
  background: var(--card);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  padding: var(--space-4);
}
```

### Pill tabs / chips

```css
.chip {
  padding: 8px 16px;
  border-radius: var(--radius-pill);
  background: var(--surface);
  color: var(--text-muted);
  font: 500 14px var(--font-sans);
  border: 1px solid transparent;
}
.chip[aria-selected="true"] {
  background: var(--card);
  color: var(--text);
  box-shadow: var(--shadow-card);
  border-color: var(--border-ui);
}
```

### Primary and secondary buttons

```css
.btn {
  min-height: 48px;
  padding: 0 24px;
  border-radius: var(--radius-pill);
  font: 600 16px var(--font-sans);
  cursor: pointer;
  transition: transform .15s ease, box-shadow .15s ease;
}
.btn-primary {
  background: linear-gradient(180deg, #3a3330, #2b2623);
  color: #fff;
  border: none;
  box-shadow: var(--shadow-card);
}
.btn-secondary {
  background: var(--surface);
  color: var(--text);
  border: 1px solid var(--border-ui);
}
.btn:active {
  transform: translateY(1px);
  box-shadow: var(--shadow-press);
}
```

### Search / input field

```css
.input {
  height: 48px;
  padding: 0 16px;
  border-radius: var(--radius-pill);
  background: var(--surface);
  border: 1px solid var(--border-ui);
  color: var(--text);
  font: 400 16px var(--font-sans);
}
.input::placeholder { color: var(--text-muted); }
```

### Focus state (never remove it)

```css
:focus-visible {
  outline: 3px solid var(--accent);
  outline-offset: 3px;
}
```

### Modal with blurred overlay

```css
.overlay {
  position: fixed; inset: 0;
  background: rgba(43, 38, 35, 0.35);
  backdrop-filter: blur(8px);
  display: grid; place-items: end center;
}
.modal {
  width: min(100%, 420px);
  background: var(--surface);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  padding: var(--space-6);
  box-shadow: var(--shadow-float);
}
```

### Neumorphic (strict) button, only if you want that variant

```css
.neu {
  background: #e6e0da;
  border-radius: 20px;
  box-shadow: 8px 8px 16px #c9c3bd, -8px -8px 16px #ffffff;
}
.neu:active {
  box-shadow: inset 6px 6px 12px #c9c3bd, inset -6px -6px 12px #ffffff;
}
```

---

## 6. Typography

| Role                 | Font                     | Size    | Weight  |
| -------------------- | ------------------------ | ------- | ------- |
| Post / card title    | EB Garamond or Cormorant | 20-24px | 500-600 |
| Hero / prompt text   | Serif                    | 18-22px | 500     |
| Body                 | Inter                    | 15-16px | 400     |
| Labels, nav, buttons | Inter                    | 12-14px | 500-600 |
| Muted meta (dates)   | Inter                    | 12-13px | 400     |

Rules:

- Never use pure `#000` on pure `#fff`. Use warm near-black on warm white.
- Keep body text at 16px or larger for readability.
- Limit to **two** font families.

---

## 7. Layout and app patterns (from your screenshot)

- **Top bar:** icon buttons in rounded squares (notifications left, menu right), logo centered.
- **Composer pill:** avatar + prompt + edit icon in one rounded bar.
- **Filter chips:** horizontally scrollable pill row.
- **Feed card:** avatar, name, timestamp, serif title, excerpt, thumbnail, then like/comment row.
- **Bottom nav:** floating rounded bar with 4 icon + label tabs; active tab uses dark text, inactive uses muted.
- **Side drawer:** slides over a dimmed, scaled-back screen; active item gets a white pill, special item (donate) gets a tinted accent pill.

Suggested spacing: screen padding 16px, gap between cards 16px, card padding 16px, nav item height 48px or more.

---

## 7.1 Responsive navigation: floating bottom bar on mobile, normal top header on laptop

Pattern from your "Drift Away" screenshot: a **floating, frosted-glass pill** pinned near the bottom of the screen, with icon + label tabs and a lighter pill behind the active tab. Use it on **mobile only**. On laptop, a normal top header is the better choice (a bottom bar is far from the cursor and wastes vertical space).

**Key idea:** write the navigation markup **once** and let CSS move it. Do not duplicate it in two places, or screen readers will announce it twice.

### HTML

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">

<header class="site-nav">
  <a class="brand" href="/">Drift</a>

  <nav aria-label="Main">
    <ul>
      <li>
        <a href="/" aria-current="page">
          <svg aria-hidden="true" width="22" height="22"><!-- home icon --></svg>
          <span>Home</span>
        </a>
      </li>
      <li>
        <a href="/trips">
          <svg aria-hidden="true" width="22" height="22"><!-- plane icon --></svg>
          <span>Trips</span>
        </a>
      </li>
      <li>
        <a href="/profile">
          <svg aria-hidden="true" width="22" height="22"><!-- user icon --></svg>
          <span>Profile</span>
        </a>
      </li>
    </ul>
  </nav>
</header>
```

### CSS (desktop first, mobile override)

```css
.site-nav {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 32px;
  background: var(--surface);
}
.site-nav .brand {
  font: 600 22px var(--font-serif);
  color: var(--text);
  text-decoration: none;
}
.site-nav ul {
  display: flex;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.site-nav li a {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 0 16px;
  border-radius: var(--radius-pill);
  color: var(--text-muted);
  font: 500 15px var(--font-sans);
  text-decoration: none;
}
.site-nav li a[aria-current="page"] {
  background: var(--card);
  color: var(--text);
  box-shadow: var(--shadow-card);
}

@media (max-width: 767px) {
  .site-nav {
    position: fixed;
    top: auto;
    left: 16px;
    right: 16px;
    bottom: calc(12px + env(safe-area-inset-bottom));
    padding: 8px;
    border-radius: var(--radius-lg);
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(255, 255, 255, 0.6);
    box-shadow: var(--shadow-float);
  }
  .site-nav .brand { display: none; }
  .site-nav nav { width: 100%; }
  .site-nav ul { justify-content: space-around; }
  .site-nav li a {
    flex-direction: column;
    justify-content: center;
    gap: 4px;
    min-width: 64px;
    min-height: 56px;
    padding: 0 12px;
    font-size: 12px;
  }
  body {
    padding-bottom: calc(96px + env(safe-area-inset-bottom));
  }
}

@supports (backdrop-filter: blur(1px)) {
  @media (max-width: 767px) {
    .site-nav {
      background: rgba(255, 255, 255, 0.6);
      backdrop-filter: blur(16px) saturate(140%);
      -webkit-backdrop-filter: blur(16px) saturate(140%);
    }
  }
}
```

### Why each piece matters

| Piece                                                    | Reason                                                                        |
| -------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `viewport-fit=cover` + `env(safe-area-inset-bottom)` | Keeps the bar above the iPhone home indicator                                 |
| `body` bottom padding                                  | Otherwise the floating bar covers the last piece of content                   |
| `@supports` for `backdrop-filter`                    | Solid fallback where blur is unsupported, so the bar never becomes unreadable |
| `aria-current="page"`                                  | Tells screen readers (and your CSS) which tab is active                       |
| `min-height: 56px`                                     | Comfortable touch target                                                      |
| Same `<nav>` for both layouts                          | One DOM, no duplicate announcements                                           |

### Rules for this component

1. **3 to 5 items maximum.** If you have more, move the rest into a drawer (like your earlier Hungarian app screenshot).
2. **Keep labels visible.** Icon-only tabs are harder to understand.
3. **Do not copy the pale label color from the screenshot.** The inactive labels there look low contrast. Use `--text-muted` (5.95:1 on white). With a translucent bar over images, test the contrast over the *worst* background behind it, or keep the bar fairly opaque.
4. **Active state must not rely on color alone.** The lighter pill behind the active tab plus darker text already does this well.
5. **Add a visible `:focus-visible` ring** to each link for keyboard users.

---

## 8. Accessibility (the part most soft UI designs get wrong)

Soft, low-contrast shadows can make it hard for users with visual impairments to tell elements apart. Critics of neumorphism raise exactly this. Build these rules in from the start.

WCAG 2.2 Level AA requirements relevant to this style:

- **Normal text:** at least 4.5:1 against its background.
- **Large text** (18pt+ or 14pt+ bold): at least 3:1.
- **UI components and meaningful graphics** (button boundaries, input borders, icons that convey state, focus rings): at least 3:1 against adjacent colors (SC 1.4.11 Non-text Contrast). This applies to hover, focus and selected states too.
- **Focus must be visible** and not hidden behind overlays.
- **Do not rely on color alone** to convey status.
- Placeholder text is not exempt from contrast requirements.

Practical rules for soft UI:

1. Shadow alone must never be the only thing that marks a control as clickable. Add a border, icon, or clear label.
2. Test muted text with a contrast checker. This is where most soft palettes fail.
3. Provide `prefers-reduced-motion` handling for animated transitions.
4. Keep touch targets at least 44-48px.
5. For modals: trap focus, close on `Esc`, use `role="dialog"` and `aria-modal="true"`.

---

## 9. Common beginner mistakes

| Mistake                                 | Why it hurts                  | Fix                                           |
| --------------------------------------- | ----------------------------- | --------------------------------------------- |
| Pure black or pure white everywhere     | Kills the soft feel           | Warm near-black and off-white                 |
| Too many accent colors                  | Looks messy                   | One accent, used sparingly                    |
| Heavy shadows (opacity above about 15%) | Looks dated and dirty         | Large blur, 8-14% opacity                     |
| Light gray muted text                   | Fails contrast                | Verify 4.5:1 or higher                        |
| Removing focus outlines                 | Keyboard users get lost       | Style `:focus-visible` instead              |
| Shadow-only buttons                     | Controls are not discoverable | Add border, label or icon                     |
| Using soft UI for dense dashboards      | Hurts scanning speed          | Use flat or dense styles for data-heavy views |
| Mixing 3+ border radii randomly         | Looks inconsistent            | Stick to 3 radius tokens                      |

---

## 10. When to use and when not to

**Good fit:** wellness and meditation apps, journaling, community or social apps, portfolio and landing pages, onboarding flows, settings screens, single-purpose tools.

**Poor fit:** DevOps dashboards, monitoring tools, data tables, admin panels, anything where users scan lots of dense information quickly.

---

## 11. Build checklist

- [ ] Tokens defined (colors, radius, shadow, spacing, fonts)
- [ ] One accent color only
- [ ] All text pairs verified at 4.5:1 or higher
- [ ] All control borders and icons verified at 3:1 or higher
- [ ] Visible `:focus-visible` style
- [ ] Shadows tinted warm and under about 15% opacity
- [ ] Two fonts maximum (serif + sans)
- [ ] Touch targets 44px or larger
- [ ] Modal is keyboard accessible
- [ ] Tested on a real phone in bright light

---

## 12. Practice project ideas

1. **Soft UI landing page** for a fictional wellness app (hero, features, pricing cards). Beginner.
2. **Community feed** clone of your screenshot with chips, cards, bottom nav, and drawer, in React. Intermediate.
3. **Design system page** documenting your tokens and components (like a mini Storybook). Intermediate.
4. **Full-stack journaling app** with a soft UI front end, AWS Lambda + API Gateway back end, and DynamoDB storage. Strong portfolio piece for cloud roles.
5. **Dark mode variant** of the same tokens. Re-verify every contrast ratio. Advanced.

---

## 13. Search keywords for inspiration

`soft UI`, `neumorphism mobile app`, `warm minimal UI`, `beige app design`, `wellness app UI`, `serif sans app design`, `iOS-style modal concept`, `bottom sheet UI`, `drawer menu concept`. Browse Dribbble, Behance and Mobbin.

---

## References

- Wikipedia, *Neumorphism* (history, characteristics, criticism): <https://en.wikipedia.org/wiki/Neumorphism>
- Interaction Design Foundation, *Neumorphism*: <https://ixdf.org/literature/topics/neumorphism>
- VP0, *What Is Soft UI Design?*: <https://vp0.com/blogs/what-is-soft-ui-design>
- UI UX Showcase, *Neumorphism glossary*: <https://uiuxshowcase.com/glossary/neumorphism/>
- Entropik, *Neumorphism in UI: The Future of Soft, Minimalist Design*: <https://www.entropik.io/blog/neumorphism-in-ui-the-future-of-soft-minimalist-design>
- The Alien Design, *Neumorphism UI*: <https://www.thealien.design/insights/neumorphism-ui>
- WebAIM, *WCAG 2.2 Overview and Feedback*: <https://webaim.org/blog/wcag-2-2-overview-and-feedback/>
- OpenReplay, *How to Check Color Contrast for WCAG*: <https://blog.openreplay.com/check-color-contrast-wcag/>
- AccessibleWeb, *Contrast ratio requirements for text and UI elements*: <https://accessibleweb.com/?p=1898>
- W3C, *WCAG 2.2*: <https://www.w3.org/TR/WCAG22/>
