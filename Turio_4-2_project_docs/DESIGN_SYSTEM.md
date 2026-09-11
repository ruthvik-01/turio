# Turio — Design System

## 1. Source

This design system adapts the supplied `DESIGN(1).md` reference into a Turio product UI. The reference emphasizes an editorial luxury feel: dark hero surfaces, bright editorial sections, restrained color, strong typography, square geometry, generous spacing, and zero decorative shadows. fileciteturn4file0L1-L6

## 2. Visual direction

Turio should feel:

- premium,
- calm,
- precise,
- technical without looking clinical,
- editorial rather than dashboard-heavy.

Use the provided reference as the visual grammar for **every small form and component**, not only the landing page.

## 3. Color tokens

Primary tokens from the supplied reference:

| Token | Value | Role |
|---|---|---|
| `--color-vault-ink` | `#191b1f` | hero/dark surfaces |
| `--color-paper-white` | `#ffffff` | main canvas |
| `--color-mist-white` | `#f6f9f9` | soft section background |
| `--color-fog-gray` | `#9fabad` | muted text |
| `--color-hairline` | `#e6ebec` | dividers/borders |
| `--color-obsidian` | `#000000` | strongest text |
| `--color-peach-wall` | `#fcede1` | feature background |
| `--color-mint-wall` | `#eefcef` | feature background |
| `--color-lavender-wall` | `#e6def0` | feature background |
| `--color-deep-teal` | `#186f64` | primary action |
| `--color-electric-violet` | `#536eff` | secondary action |
| `--color-royal-violet` | `#644bc4` | secondary accent |
| `--color-sapphire-blue` | `#154ea5` | tertiary action |

The supplied reference explicitly reserves the strong brand colors for action moments and keeps body surfaces restrained. fileciteturn4file0L10-L24

## 4. Typography

Reference type scale:

- caption: 13px
- body: 16px
- subheading: 22px
- heading-sm: 28px
- heading: 46px
- display: 80px

The reference uses a sans body register and high-contrast serif headlines. Use substitute fonts where licensed fonts are unavailable. fileciteturn4file0L26-L52

For implementation:

- body: Inter / system sans,
- display fallback: Playfair Display / another licensed editorial serif.

Do not ship unlicensed font files.

## 5. Spacing

Base unit: 4px.

Use:

```text
8 / 12 / 16 / 24 / 32 / 48 / 64 / 72
```

Reference layout:

- max content width: ~1200px
- section gap: 64–96px
- card padding: 32px
- element gap: 16px

fileciteturn4file0L54-L86

## 6. Shapes

Reference shape language is extremely sharp:

- cards: 0px radius
- inputs: 2px
- buttons: 2px
- tags: 2px

No pill UI. No oversized rounded cards. fileciteturn4file0L73-L80

## 7. Elevation

**No decorative box shadows.**

Use:
- surface contrast,
- hairline borders where needed,
- spacing,
- typography,
- imagery.

The reference explicitly uses a shadowless system. fileciteturn4file0L152-L158

## 8. Buttons

Primary button:

```text
background #186f64
white text
2px radius
12px vertical
27px horizontal
no shadow
no gradient
```

Secondary:

```text
#536eff
white text
2px radius
```

Tertiary:

```text
#154ea5
white text
2px radius
```

These dimensions and constraints come directly from the supplied reference. fileciteturn4file0L101-L114

## 9. Forms

Every small form must follow the same visual language:

- 2px radius,
- minimal border/hairline,
- 16px body text,
- 13px helper/caption text,
- generous vertical spacing,
- no filled gray input shells unless state requires it,
- no heavy shadows,
- clear focus state,
- primary action isolated.

## 10. Application assistant panel

Use editorial whitespace.

Example:

```text
APPLICATION

Your application is almost ready.

Most of your information is already stored.
We need two additional details.

[ Work authorization field ]

[ Sponsorship field ]

Continue →
```

Do not make this a dense wizard with ten cards.

## 11. Progress

Prefer a simple horizontal sequence:

```text
Profile → Match → Prepare → Review → Apply
```

Use a thin line and restrained status indicators.

## 12. Imagery

The supplied reference uses 3D metallic/prismatic renders as a signature visual. fileciteturn4file0L136-L140

For Turio, use abstract 3D visual language sparingly and reinterpret the material language around:
- chrome,
- translucent glass,
- prismatic surfaces,
- subtle orbital shapes.

Do not use decorative 3D art inside every dashboard panel.

## 13. Do

- large whitespace,
- clean type hierarchy,
- squared geometry,
- strong dark/light transitions,
- restrained accents,
- editorial headings,
- simple one-action screens.

## 14. Don't

- no glassmorphism everywhere,
- no pill-shaped buttons,
- no giant card grids,
- no excessive gradients,
- no glow around every button,
- no dark-mode-only UI,
- no technical telemetry exposed by default,
- no rainbow AI effects.

## 15. Reference-derived rule

The supplied design says the visual system's strength comes from typography, surfaces, spacing and controlled visual moments rather than decorative UI effects. Apply that principle consistently to Turio. fileciteturn4file0L170-L180
