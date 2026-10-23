# Turio — Design System Tokens

## Status

This file is a **supporting design-token reference**. `FRONTEND.md` owns screen structure and visual direction.

Do not use this file to introduce a competing layout or navigation model.

## 1. Font roles

```css
--font-ui: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
--font-display: var(--font-ui);
```

Use the approved system fonts already available. The primary Turio mark remains the supplied image asset; the existing footer text may be enlarged decoratively on landing under ADR-048, not substituted for that asset.

## 2. Base colors

ADR-048 approves paired neutral palettes; the supplied green logo stays unchanged.

| Token | Light | Dark |
| --- | --- | --- |
| `--canvas` | `#f5f5f3` | `#141413` |
| `--surface` | `#fafaf8` | `#1d1d1b` |
| `--ink` | `#1a1a1a` | `#f4f4ef` |
| `--muted` | `#63635b` | `#b6b6ad` |
| `--hairline` | `#d5d5d0` | `#41413b` |
| `--boundary` | `#85857e` | `#939388` |

`--accent` follows ink and `--on-accent` follows canvas for neutral actions. Status/chart roles remain semantic, labelled and independently readable. Decoration uses original sage/stone gradients only on public landing/auth, not data workspaces.

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

Use only slow CSS transform/opacity atmosphere on landing/auth, with a clear reading area. Freeze it for reduced motion and suppress it for reduced transparency, increased contrast and forced colours. No decorative animation behind protected workspace data.

## 8. Accessibility

Do not rely on green, cream, or glass effects alone to communicate state. Pair color with labels, icons, text, borders, or structure.
