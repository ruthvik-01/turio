# Turio — Design System Tokens

## Status

This file is a **supporting design-token reference**. `FRONTEND.md` owns screen structure and visual direction.

Do not use this file to introduce a competing layout or navigation model.

## 1. Font roles

```css
--font-ui: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
--font-display: Georgia, "Times New Roman", serif;
```

Use the actual approved product fonts available to the implementation. Never recreate the Turio wordmark with text; use the brand asset.

## 2. Base colors

The approved frontend direction uses:

- `--canvas`: soft cream/near-white
- `--surface`: white/off-white
- `--ink`: deep navy/charcoal
- `--muted`: soft gray-green/gray
- `--hairline`: low-contrast neutral border
- `--green-deep`: primary natural green derived consistently from the brand palette
- `--green-soft`: pale green surface
- `--cream-soft`: pale cream surface

Exact values may be frozen during implementation, but they must remain within the approved cream/green visual family unless an ADR explicitly changes the direction.

## 3. Logo tokens

Brand colors:

```text
--logo-leaf: approximately #93B183
--logo-forest: approximately #3D5741
```

These values are guidance extracted from the supplied logo reference. If an official vector source exists, use that source as authoritative.

The UI green used next to the logo should be derived from the brand forest family rather than introducing an unrelated green.

## 4. Shape

- Large panels: 20–28px range where visually appropriate.
- Standard cards: 16–20px.
- Inputs: 10–14px.
- Primary buttons: pill/large rounded ends.
- Small utility controls: 10–12px.

Do not mix arbitrary radius values across a screen.

## 5. Glass material

Use only where the approved reference shows or benefits from a frosted surface:

```text
background: semi-transparent light surface
backdrop-filter: blur()
border: thin low-contrast hairline
shadow: soft and restrained
```

Never use heavy blur behind text that harms readability.

## 6. Spacing

Use an 8px base rhythm:

```text
4  8  12  16  24  32  48  64  80
```

Prefer generous spacing over compact density.

## 7. Motion

Motion should be short, smooth, and purposeful:
- navigation state,
- hover/focus,
- loading/progress,
- checklist transitions,
- page transitions where they aid continuity.

Avoid perpetual animation and decorative movement that competes with content.

## 8. Accessibility

Do not rely on green, cream, or glass effects alone to communicate state. Pair color with labels, icons, text, borders, or structure.
