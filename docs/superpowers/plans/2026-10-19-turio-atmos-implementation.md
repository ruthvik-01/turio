# Turio Atmos Implementation Plan

> **For agentic workers:** Use the executing-plans skill for native execution, or subagent-driven-development if the user selects per-task agents. Follow the checkboxes; read the linked spec first. No commits, pushes or deployment without a separate request.

**Goal:** Apply the selected lightweight Atmos-inspired design to all 13 existing Turio routes while preserving application behaviour and staged work.

**Architecture:** Existing global CSS and shared shell already cover every screen. Add a small independent theme helper/toggle and one decorative root layer; change presentation rules instead of rewriting screen components. Keep SessionProvider, APIs, data, route wrappers and business logic unchanged.

**Tech Stack:** Existing Next.js 16, React 19, TypeScript, Tailwind CSS 4, Node built-in assertions, Python/Playwright rendered verifier. No new packages.

**Spec:** [Turio Atmos Redesign](../specs/2026-10-19-turio-atmos-design.md).

## Global constraints

- All 13 existing routes; no sidebar, new screens, palette-generation feature or new backend service.
- Original CSS/SVG atmosphere only on landing/login/signup; no WebGL, GSAP, Three.js, Lenis, copied assets or commercial font download.
- Preserve the existing green logo, navigation/auth actions, consent, bulk Stop/approval, revisions and reviewed-submission/expiry/uncertain-outcome safeguards.
- System sans; landing headings 40px desktop/28px mobile, page headings 28px/24px, body 15px, editable fields at least 16px; display weight 500–600.
- Desktop/mobile gutters 24px/16px; interactive targets at least 44px. Workspace panels mostly opaque; header may be translucent.
- Light canvas/surface/ink/muted/border/input boundary: #f5f5f3/#fafaf8/#1a1a1a/#63635b/#d5d5d0/#85857e. Dark equivalents: #141413/#1d1d1b/#f4f4ef/#b6b6ad/#41413b/#939388.
- Saved validated `turio-theme` overrides system preference; storage failure still permits an in-memory choice. Only controlled html theme-attribute differences may suppress hydration warnings.
- Reduced motion is static; reduced transparency, increased contrast and forced colours use readable solid materials.
- Preserve all pre-existing staged work. Inspect focused diffs; never reset, restore or stage unrelated files. Human/live/research acceptance gates remain open.

## Review focus

1. Opposed saved/system themes must paint correctly before hydration, including reload/navigation.
2. Invalid or blocked storage must not crash startup or undo a clicked theme.
3. Narrow headers must preserve real pointer/keyboard navigation and visible skip links.
4. Dark states must keep readable controls, statuses, charts and accessible data tables.
5. Decorative layers must not intercept controls or remain animated in accessibility modes.

## Execution choice

**Native execution recommended for speed:** implement the three sequential tasks in this session, then use one fresh reviewer on the final scoped diff. Per-task implementer/reviewer agents are an alternative, with additional context cost. Approval of this plan authorizes the recommended native method unless the user requests the alternative.

## Task 1: Theme foundation

**Files:** create [frontend/lib/theme.ts](../../../frontend/lib/theme.ts) and [scripts/check_theme.cjs](../../../scripts/check_theme.cjs); modify [layout.tsx](../../../frontend/app/layout.tsx), [ui.tsx](../../../frontend/components/ui.tsx) and [globals.css](../../../frontend/app/globals.css). Fold the required direction record into [ADR.md](../../ADR.md), [FRONTEND.md](../../FRONTEND.md) and [DESIGN_SYSTEM.md](../../DESIGN_SYSTEM.md) before product edits.

**Interfaces:** `Theme = "light" | "dark"`; `resolveTheme(saved: unknown, prefersDark: boolean): Theme`; `applyTheme(theme: Theme): void`; `THEME_BOOTSTRAP: string`; internal `ThemeToggle(): React.JSX.Element`. Theme state does not enter SessionProvider.

- [x] Read frontend/AGENTS.md and the installed Next script/CSS docs. Record the selected direction in the owning docs without marking delivery verified.
- [x] Add the failing Node check below and run `node scripts/check_theme.cjs`. Before the helper exists, the missing-module failure is expected; record the actual result.

```js
const assert = require("node:assert/strict");
const vm = require("node:vm");
const { resolveTheme, applyTheme, THEME_BOOTSTRAP } = require("../frontend/lib/theme.ts");
for (const saved of [null, undefined, "invalid", {}, 1]) {
  assert.equal(resolveTheme(saved, false), "light");
  assert.equal(resolveTheme(saved, true), "dark");
}
for (const saved of ["light", "dark"]) {
  assert.equal(resolveTheme(saved, false), saved);
  assert.equal(resolveTheme(saved, true), saved);
  const document = { documentElement: { dataset: {} } };
  vm.runInNewContext(THEME_BOOTSTRAP, { document, localStorage: { getItem: () => saved } });
  assert.equal(document.documentElement.dataset.theme, saved);
}
for (const getItem of [() => "invalid", () => { throw Error("blocked"); }]) {
  const document = { documentElement: { dataset: {} } };
  vm.runInNewContext(THEME_BOOTSTRAP, { document, localStorage: { getItem } });
  assert.equal(document.documentElement.dataset.theme, undefined);
}
global.document = { documentElement: { dataset: {} } };
global.localStorage = { setItem() { throw Error("blocked"); } };
applyTheme("dark");
assert.equal(global.document.documentElement.dataset.theme, "dark");
console.log("theme checks passed");
```

- [x] Implement the small pure/helper module; no browser work at module import time.

```ts
export type Theme = "light" | "dark";
export function resolveTheme(saved: unknown, prefersDark: boolean): Theme {
  return saved === "light" || saved === "dark" ? saved : prefersDark ? "dark" : "light";
}
export const THEME_BOOTSTRAP = `(()=>{let t;try{t=localStorage.getItem('turio-theme')}catch{}
if(t==='light'||t==='dark')document.documentElement.dataset.theme=t;})();`;
export function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme;
  try { localStorage.setItem("turio-theme", theme); } catch {}
}
```

- [x] Integrate the trusted synchronous bootstrap before body content; retain every existing body child and provider. Installed Next beforeInteractive means before hydration, not an explicit first-paint guarantee.

```tsx
import { THEME_BOOTSTRAP } from "@/lib/theme";
// Inside existing RootLayout; keep existing imports and metadata.
<html lang="en" suppressHydrationWarning>
  <head><script id="turio-theme" dangerouslySetInnerHTML={{ __html: THEME_BOOTSTRAP }} /></head>
  <body><SessionProvider><a className="skip-link" href="#main-content">Skip to content</a>
    <Header /><div id="main-content">{children}</div>
    <footer className="site-footer"><span>Turio</span><span>Review before submitting.</span></footer>
  </SessionProvider></body>
</html>
```

- [x] Add ThemeToggle next to, not instead of, the current header actions. Existing ui.tsx already imports useEffect/useState.

```tsx
import { applyTheme, resolveTheme, type Theme } from "@/lib/theme";
function ThemeToggle() {
  const [theme, setTheme] = useState<Theme | null>(null);
  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const sync = () => setTheme(resolveTheme(document.documentElement.dataset.theme, media.matches));
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, []);
  return <button id="turio-theme-toggle" type="button" className="text-button theme-toggle"
    aria-label="Dark theme" aria-pressed={theme === null ? undefined : theme === "dark"}
    disabled={theme === null} onClick={() => {
      const next = theme === "dark" ? "light" : "dark";
      applyTheme(next); setTheme(next);
    }}>Theme</button>;
}
```

- [x] Replace root palette values and hard-coded cream/white/green glass fills with semantic tokens. Keep chart values/series/shapes, warning/error roles and existing accessibility fallbacks. Primary labels use `--on-accent`, not hard-coded white.

```css
:root { color-scheme:light; --canvas:#f5f5f3; --surface:#fafaf8; --ink:#1a1a1a;
  --muted:#63635b; --hairline:#d5d5d0; --boundary:#85857e;
  --accent:var(--ink); --on-accent:var(--canvas); --header-fill:rgb(245 245 243 / .8); }
@media (prefers-color-scheme:dark) {
  :root:not([data-theme="light"]) { color-scheme:dark; --canvas:#141413; --surface:#1d1d1b;
    --ink:#f4f4ef; --muted:#b6b6ad; --hairline:#41413b; --boundary:#939388;
    --header-fill:rgb(20 20 19 / .8); }
}
:root[data-theme="dark"] { color-scheme:dark; --canvas:#141413; --surface:#1d1d1b;
  --ink:#f4f4ef; --muted:#b6b6ad; --hairline:#41413b; --boundary:#939388;
  --header-fill:rgb(20 20 19 / .8); }
.primary { color:var(--on-accent); background:var(--accent); }
```

- [x] Run the Node check and `npm --prefix frontend run typecheck -- --incremental false`. Record actual results; leave changes uncommitted.

## Task 2: Shared Atmos skin and original decoration

**Files:** modify [globals.css](../../../frontend/app/globals.css), [layout.tsx](../../../frontend/app/layout.tsx) and [verify_apple_redesign.py](../../../frontend/tests/verify_apple_redesign.py). No landing/auth/dashboard component rewrite or route-wrapper edit is needed: existing classes already provide the structure.

**Consumes:** Task 1 palette/helper, existing `.site-header`, `.header-actions`, `.container`, `.workspace`, `.panel`, `.button`, `.tabs`, `.job-card`, `.filters`, `.form-panel`, `.resume-upload`, `.review-box`, `.data-table`, `.chart-panel`, `main.landing` and `main.auth-layout`.

**Produces:** `.atmosphere` decorative root layer and `.footer-wordmark` on the existing footer Turio span; 13-route shared presentation.

- [x] First update intentional visual assertions in the existing rendered verifier and run it against the pre-skin dev server to record a genuine RED result. Keep all business/accessibility checks.

```python
# In main(url, output), qualify the existing theme/viewport/route loops and names.
expected_canvas = {"light": "rgb(245, 245, 243)", "dark": "rgb(20, 20, 19)"}
# Add this outer loop around existing width/path loops in main(url, output).
for theme in ("light", "dark"):
    context = await browser.new_context(color_scheme=theme, service_workers="block")
    await context.add_init_script(f"localStorage.setItem('turio-theme', '{theme}')")
    await context.route("**/*", intercept)
    page = await context.new_page()
    page.set_default_timeout(7000)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if "hydrat" in m.text.lower() else None)
    # Keep existing response/requestfailed listeners and width/path loop bodies here.
    # At the end of that theme's full route loop:
    await context.close()
# Within preserved width/path loop, qualify each check/screenshot name:
label = f"{theme} {width} {path}"
check(label + " neutral canvas", styles["background"] == expected_canvas[theme], styles["background"])
check(label + " sans heading", "Georgia" not in styles["font"] and "Times" not in styles["font"]
      and 500 <= int(styles["weight"]) <= 600, styles["font"])
# Replace only obsolete glass-all-cards assertions; require opaque workspace panels.
check(label + " opaque workspace panel", glass["filter"] == "none"
      and not glass["background"].startswith("rgba("), glass)
```

- [x] Change the existing CSS rules in place: inset sticky pill header (24/16px gutters), preserved nav wrap/scroll order and stacking, 44px targets, pill buttons/tabs, 18–24px opaque workspace cards, restrained 40/28px hero and 28/24px page headings. Tokenize current hard-coded borders/shadows/chart-grid/dropdown shadows; preserve non-colour chart encodings and accessible tables.
- [x] Add one pointer-inert decorative div and original SVG grain in root layout. It stays outside main-content and owns no data/events. Add footer-wordmark to the existing span; do not duplicate the footer.

```tsx
<div className="atmosphere" aria-hidden="true">
  <svg className="atmosphere-grain" width="100%" height="100%">
    <filter id="turio-grain"><feTurbulence type="fractalNoise" baseFrequency=".65"
      numOctaves="3" stitchTiles="stitch" /><feColorMatrix type="saturate" values="0" /></filter>
    <rect width="100%" height="100%" filter="url(#turio-grain)" />
  </svg>
</div>
```

```css
:root { --atmosphere-sage:rgb(145 161 138 / .5); --atmosphere-stone:rgb(194 189 167 / .5); }
@media(prefers-color-scheme:dark) {
  :root:not([data-theme="light"]) { --atmosphere-sage:rgb(75 97 70 / .5); --atmosphere-stone:rgb(113 104 78 / .5); }
}
:root[data-theme="dark"] { --atmosphere-sage:rgb(75 97 70 / .5); --atmosphere-stone:rgb(113 104 78 / .5); }
body { isolation:isolate; }
.atmosphere { display:none; position:fixed; inset:0; z-index:-1; overflow:hidden; pointer-events:none;
  mask-image:radial-gradient(ellipse 45% 30% at 50% 48%,transparent 55%,#000 100%); }
body:has(main.landing) .atmosphere, body:has(main.auth-layout) .atmosphere { display:block; }
.atmosphere::before { content:""; position:absolute; inset:-25%;
  background:radial-gradient(ellipse at 20% 30%,var(--atmosphere-sage),transparent 55%),
    radial-gradient(ellipse at 80% 70%,var(--atmosphere-stone),transparent 55%);
  filter:blur(40px); animation:atmosphere-drift 28s ease-in-out infinite alternate; }
.atmosphere-grain { position:absolute; inset:0; opacity:.045; }
@keyframes atmosphere-drift { to { transform:rotate(14deg) scale(1.08); opacity:.75; } }
body:has(main.landing) .footer-wordmark { font-size:clamp(64px,16vw,224px); line-height:1; }
@media(prefers-reduced-motion:reduce) { .atmosphere::before { animation:none; } }
@media(prefers-reduced-transparency:reduce), (prefers-contrast:more), (forced-colors:active) {
  .atmosphere { display:none!important; }
}
```

- [x] Keep the centre clear with a canvas-colour radial mask/overlay so text contrast remains stable; use decorative colour tokens with coherent dark values. Only transforms/opacity animate. Existing SVG failure still leaves gradients. Compact footer remains on auth/protected routes.
- [x] Run the full 78-render light/dark matrix and typecheck. Preserve descriptive headings, touch targets, form labels, company autocomplete, consent/review/bulk guards and independent Home loading/error checks. Do not remove assertions to get GREEN.

## Task 3: Edge cases, production proof and handoff

**Files:** finish [verify_apple_redesign.py](../../../frontend/tests/verify_apple_redesign.py); update [PROJECT_CONTEXT.md](../../PROJECT_CONTEXT.md), [PROGRESS.md](../../PROGRESS.md) and shared daily topic with actual outcomes. No backend/database/service code changes.

- [x] Extend the existing check(name, result, detail) runner with all five Review Focus cases. Capture hydration-related console warnings as failures, not just page errors.

```python
# Define inside existing main(url, output), after intercept/check, and call before its route matrix.
async def theme_case(browser, system, saved, blocked=False):
    state["public"] = True
    ctx = await browser.new_context(color_scheme=system, service_workers="block")
    await ctx.route("**/*", intercept)
    p = await ctx.new_page()
    p.on("pageerror", lambda e: errors.append(str(e)))
    p.on("console", lambda m: errors.append(m.text) if "hydrat" in m.text.lower() else None)
    await p.goto(url + "/login")
    if saved is not None:
        await p.evaluate("t=>localStorage.setItem('turio-theme',t)", saved)
    # Seed once before reload; never reset a clicked preference on every document.
    if blocked:
        await ctx.add_init_script("""Storage.prototype.getItem=function(){throw Error('blocked')};
        Storage.prototype.setItem=function(){throw Error('blocked')};""")
    await ctx.add_init_script("""requestAnimationFrame(function capture(){
      if(!document.body){requestAnimationFrame(capture);return}
      window.__firstTheme={theme:document.documentElement.dataset.theme,
        background:getComputedStyle(document.body).backgroundColor};
    });""")
    await p.reload()
    await p.wait_for_function("window.__firstTheme && document.querySelector('#turio-theme-toggle')?.disabled===false")
    current = saved if saved in ("light", "dark") and not blocked else system
    label = f"theme {system}/{saved}/blocked={blocked}"
    first = await p.evaluate("window.__firstTheme")
    check(label + " first paint", first.get("theme") == (current if saved in ("light", "dark") and not blocked else None))
    opposite = "light" if current == "dark" else "dark"
    await p.get_by_role("button", name="Dark theme", exact=True).click()
    check(label + " toggle", await p.locator("html").get_attribute("data-theme") == opposite)
    await p.reload()
    if blocked:
        check(label + " blocked reload", await p.locator("html").get_attribute("data-theme") is None)
    else:
        check(label + " saved reload", await p.locator("html").get_attribute("data-theme") == opposite)
        await p.goto(url + "/signup")
        check(label + " navigation", await p.locator("html").get_attribute("data-theme") == opposite)
    await ctx.close()

# In the existing async_playwright/browser block before the width/path matrix:
await theme_case(browser, "light", "dark")
await theme_case(browser, "dark", "light")
await theme_case(browser, "dark", "invalid")
await theme_case(browser, "dark", None, blocked=True)
```

- [x] Assert theme survives normal reload and route navigation; invalid stored strings do not become html attributes. Check 390px pointer/keyboard nav and skip-link, 44px toggle, panel/notice/status/input contrast, unchanged chart counts/tables/shapes, pointer-events:none decoration, no decoration on protected routes and static/suppressed accessibility-mode fields.
- [x] Use an isolated loopback frontend server at port 13002. Check port availability before starting it; use dev for RED/iteration, stop only that owned server, then use the freshly built production server on the same port for final proof. Existing 13000 stack stays untouched.

```powershell
npm --prefix "D:/College/4-2 project/frontend" run dev -- --hostname 127.0.0.1 --port 13002
node scripts/check_theme.cjs
npm --prefix "D:/College/4-2 project/frontend" run typecheck -- --incremental false
npm --prefix "D:/College/4-2 project/frontend" run build
# After stopping the owned dev server; do not run both on the same port:
npm --prefix "D:/College/4-2 project/frontend" run start -- --hostname 127.0.0.1 --port 13002
& "D:/College/4-2 project/backend/.venv/Scripts/python.exe" "D:/College/4-2 project/frontend/tests/verify_apple_redesign.py" --url http://127.0.0.1:13002 --output "D:/College/4-2 project/docs/evidence/turio-atmos"
```

- [x] Run existing focused skip-link and glass-navigation regressions against the isolated server using their documented arguments. Inspect representative landing/auth/Home/Jobs/review screenshots in both themes; human visual approval remains separate from programmatic results.
- [x] Obtain one fresh review of the final scoped diff, resolve confirmed issues, then rerun affected checks. No review-agent result substitutes for a fresh test run.
- [x] Record only actual checks, failures, screenshot paths, processes and remaining limits. Update project status and shared daily topic/index; read them back. Leave source and docs uncommitted; no live employer submission or research gate closure.

## Execution amendments

- Added [next.config.ts](../../../frontend/next.config.ts) with fixed TURIO_UI_VERIFY output isolation; Next generated matching tsconfig/next-env type paths. Default output remains unchanged. This protects normal stack assets during local verification.
- Expanded the existing focused navigation verifier to cover actual text bounds, pointer theme selection and client navigation; non-shrinking anchors fixed a screenshot-detected mobile defect. Main verifier now includes computed contrast/status and atmosphere accessibility/motion cases.
- Explicit Fable reviewer was unavailable (API400); fresh review used the working session model. Its two acceptance-coverage gaps were closed; physical-device/native-backend/normal-stack coexistence is not claimed.

## Approval boundary

Native execution completed 2026-10-20: theme/config25, typecheck/build, rendered1202, navigation15 and skip3 checks passed. Preserve uncommitted changes and review the UI; no live employer/backend/research acceptance follows from synthetic checks. Execution details and rulings are in the shared 19–20 October topics.
