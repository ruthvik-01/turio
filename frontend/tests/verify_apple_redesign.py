"""Rendered redesign regression. Run with backend/.venv Python; no live APIs.
Breaks caught: theme/first-paint drift, promotional copy, missing material fallbacks,
clipped controls, intercepted decoration, lost consent, and coupled Home reads.
All network requests are intercepted; only loopback pages/static assets pass.
"""
import argparse
import asyncio
import copy
import json
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright


CONTRAST_JS = """() => {
  const rgb = value => {const n=value.match(/[\\d.]+/g)?.map(Number);return n ? [n[0],n[1],n[2],n[3]??1] : [0,0,0,0]};
  const lum = c => c.slice(0,3).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
  const ratio = (a,b) => {const l=[lum(a),lum(b)].sort((a,b)=>a-b);return (l[1]+.05)/(l[0]+.05)};
  const background = e => {
    let c=rgb(getComputedStyle(document.body).backgroundColor);
    const chain=[];for(let p=e;p&&p!==document.body;p=p.parentElement)chain.push(p);
    for(const p of chain.reverse()){const a=rgb(getComputedStyle(p).backgroundColor);c=[0,1,2].map(i=>a[i]*a[3]+c[i]*(1-a[3]));}
    return c;
  };
  const failures=[];
  const nodes=[...document.querySelectorAll('main h1,main p,main label,main input:not([type=checkbox]),main select,main textarea,main .muted,main .status,main .notice,main .badge,main .button,main .text-button')]
    .filter(e=>e.getClientRects().length&&!e.matches(':disabled')&&!e.closest('[aria-hidden=true]'));
  for(const e of nodes){
    const s=getComputedStyle(e), bg=background(e), size=parseFloat(s.fontSize);
    const threshold=size>=24||(size>=18.66&&parseInt(s.fontWeight)>=700)?3:4.5;
    const text=ratio(rgb(s.color),bg);
    const label=(e.getAttribute('aria-label')||e.textContent||e.tagName).trim().slice(0,60);
    if(text+.01<threshold)failures.push({label,kind:'text',ratio:text,threshold});
    if(['INPUT','SELECT','TEXTAREA'].includes(e.tagName)){
      const border=ratio(rgb(s.borderTopColor),bg);
      if(border+.01<3)failures.push({label,kind:'boundary',ratio:border,threshold:3});
    }
  }
  return failures;
}"""


async def main(url, output):
    origin = urlparse(url)
    assert origin.hostname in {"127.0.0.1", "localhost"}
    output.mkdir(parents=True, exist_ok=True)
    checks, failures, unexpected, errors, requests, asset_errors = [], [], [], [], [], []
    state = {"public": False, "empty": False, "error": False, "delay": False}
    release = asyncio.Event()
    long = "Synthetic exceptionally long international research engineering company " * 3
    job = dict(id="fixture-job", title="Synthetic platform engineer " * 8, company=long,
        location="Synthetic City", description="Source-backed fixture. " * 150,
        ats="ashby", required_skills=["Python", "TypeScript"], company_logo_url=None,
        job_url="https://employer.invalid/job", application_url="https://employer.invalid/job")
    profile = dict(id="fixture-profile", version=1, full_name="Synthetic Candidate",
        phone=None, contact_email="synthetic@example.invalid", location="Synthetic City",
        summary="Synthetic professional summary", linkedin_url=None, github_url=None,
        portfolio_url=None, preferred_roles=[], work_authorization_status=None,
        sponsorship_required=None, certifications=[], achievements=[],
        skills=[dict(name="Python", normalized_name="python")], experiences=[], educations=[], projects=[])
    app = dict(id="fixture-app", job=job, application_url=job["application_url"],
        status="ready_for_review", outcome="interview", notes=None, resume_id="fixture-resume",
        profile_version=1, manual_submission_required=False, readiness_score=1,
        missing_fields=[], submission_method=None, submitted_at=None, created_at="2026-10-14T00:00:00Z",
        review_token="a" * 64, events=[], fields=[dict(id="name", field_key="name", label="Full name",
        input_type="text", required=True, normalized_intent="full_name", options=[],
        value="Synthetic Candidate", value_source="profile", user_confirmed=True)])
    match = dict(id="fixture-match", job=job, final_score=.75, method="keyword", model_name="fixture",
        explanation=dict(summary="Synthetic evidence", scores={"skills": .75},
        disclaimer="Relevance, not hiring probability", matched_skills=["Python"], missing_skills=[]))
    summary = dict(total=6, interviews=1, offers=1, in_progress=3, submitted=2, cancelled=1,
        days=[dict(date=f"2026-09-{i:02d}", count=2 if i == 28 else 0) for i in range(1, 29)])

    async def intercept(route):
        req = route.request
        parsed = urlparse(req.url)
        if parsed.netloc != origin.netloc:
            unexpected.append(req.url)
            await route.abort()
            return
        path = parsed.path
        if not path.startswith("/api/"):
            if req.method != "GET":
                unexpected.append(req.url)
                await route.abort()
            else:
                await route.continue_()
            return
        requests.append(dict(path=path, method=req.method))
        if path == "/api/auth/me" and state["public"]:
            await route.fulfill(status=401, json=dict(data=None, error=dict(code="UNAUTHORIZED", message="Synthetic signed-out session")))
            return
        if state["error"] and path == "/api/jobs":
            await route.fulfill(status=503, json=dict(data=None, error=dict(code="FIXTURE", message="Synthetic inventory unavailable")))
            return
        if state["delay"] and path in {"/api/jobs", "/api/matches"}:
            await release.wait()
        if path == "/api/auth/me": data = dict(id="fixture-user", email="synthetic@example.invalid")
        elif path in {"/api/auth/login", "/api/auth/register"}:
            await route.fulfill(status=401, json=dict(data=None, error=dict(code="FIXTURE", message="Synthetic sign-in rejected")))
            return
        elif path == "/api/profiles/me": data = profile
        elif path == "/api/resumes/latest": data = dict(id="fixture-resume", checksum="fixture", original_filename="synthetic.pdf")
        elif path == "/api/applications/summary": data = summary
        elif path == "/api/jobs/companies": data = dict(companies=[dict(company=long, slug="synthetic")], total=1)
        elif path == "/api/jobs": data = dict(jobs=[] if state["empty"] else [job], total=0 if state["empty"] else 1, offset=0, limit=12)
        elif path == "/api/jobs/fixture-job": data = job
        elif path == "/api/matches": data = dict(matches=[] if state["empty"] else [match], total=0 if state["empty"] else 1, stale=False)
        elif path == "/api/matches/fixture-match": data = match
        elif path == "/api/applications": data = dict(applications=[] if state["empty"] else [app], total=0 if state["empty"] else 1)
        elif path == "/api/applications/fixture-app/capability": data = dict(available=True, reason=None)
        elif path == "/api/applications/fixture-app": data = app
        else:
            unexpected.append(path)
            await route.fulfill(status=404, json=dict(data=None, error=dict(code="FIXTURE", message="Unexpected API blocked")))
            return
        await route.fulfill(json=dict(data=copy.deepcopy(data), error=None))

    def check(name, result, detail=None):
        if result: checks.append(name)
        else: failures.append(dict(check=name, detail=detail))

    async def theme_case(browser, system, saved, blocked=False):
        state["public"] = True
        ctx = await browser.new_context(color_scheme=system, service_workers="block")
        await ctx.route("**/*", intercept)
        p = await ctx.new_page()
        p.set_default_timeout(7000)
        p.on("pageerror", lambda e: errors.append(str(e)))
        p.on("console", lambda m: errors.append(m.text) if "hydrat" in m.text.lower() else None)
        await p.goto(url + "/login")
        if saved is not None:
            await p.evaluate("t=>localStorage.setItem('turio-theme',t)", saved)
        if blocked:
            await ctx.add_init_script("""Storage.prototype.getItem=function(){throw Error('blocked')};
                Storage.prototype.setItem=function(){throw Error('blocked')};""")
        await ctx.add_init_script("""requestAnimationFrame(function capture(){
          if(!document.body){requestAnimationFrame(capture);return}
          window.__firstTheme={theme:document.documentElement.dataset.theme,
            background:getComputedStyle(document.body).backgroundColor};
        });""")
        await p.reload()
        label = f"theme {system}/{saved}/blocked={blocked}"
        try:
            await p.wait_for_function("window.__firstTheme && document.querySelector('#turio-theme-toggle')?.disabled===false", timeout=7000)
        except Exception:
            check(label + " control hydrated", False, "Theme toggle missing or disabled")
            await ctx.close()
            return
        current = saved if saved in ("light", "dark") and not blocked else system
        first = await p.evaluate("window.__firstTheme")
        check(label + " first paint preference", first.get("theme") == (current if saved in ("light", "dark") and not blocked else None), first)
        expected = "rgb(20, 20, 19)" if current == "dark" else "rgb(245, 245, 243)"
        check(label + " first paint canvas", first["background"] == expected, first)
        check(label + " initial theme", await p.get_by_role("button", name="Dark theme", exact=True).get_attribute("aria-pressed") == str(current == "dark").lower())
        opposite = "light" if current == "dark" else "dark"
        await p.get_by_role("button", name="Dark theme", exact=True).click()
        check(label + " toggle", await p.locator("html").get_attribute("data-theme") == opposite)
        await p.reload()
        await p.get_by_role("button", name="Dark theme", exact=True).wait_for()
        if blocked:
            check(label + " blocked reload", await p.locator("html").get_attribute("data-theme") is None)
            check(label + " system fallback", await p.locator("html").evaluate("e=>getComputedStyle(e).colorScheme") == system)
        else:
            check(label + " saved reload", await p.locator("html").get_attribute("data-theme") == opposite)
            await p.goto(url + "/signup")
            check(label + " navigation", await p.locator("html").get_attribute("data-theme") == opposite)
        await ctx.close()

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        await theme_case(browser, "light", "dark")
        await theme_case(browser, "dark", "light")
        await theme_case(browser, "dark", "invalid")
        await theme_case(browser, "dark", None, blocked=True)
        context = await browser.new_context(service_workers="block")
        await context.route("**/*", intercept)
        page = await context.new_page()
        page.set_default_timeout(7000)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if "hydrat" in m.text.lower() else None)
        page.on("response", lambda r: asset_errors.append(dict(url=r.url, status=r.status)) if '/_next/static/' in r.url and r.status >= 400 else None)
        page.on("requestfailed", lambda r: asset_errors.append(dict(url=r.url, failure=r.failure)) if '/_next/static/' in r.url else None)
        routes = ["/", "/login", "/signup", "/home", "/jobs", "/jobs/fixture-job?match=fixture-match",
            "/profile", "/onboarding", "/applications", "/applications/fixture-app",
            "/applications/fixture-app/review", "/interviews", "/resources"]
        state["public"] = True
        await page.goto(url + "/login")
        for theme, width in [(t, w) for t in ["light", "dark"] for w in [390, 768, 1280]]:
            await page.emulate_media(color_scheme=theme)
            await page.evaluate("t=>localStorage.setItem('turio-theme',t)", theme)
            await page.set_viewport_size(dict(width=width, height=900))
            for path in routes:
                state["public"] = path in {"/", "/login", "/signup"}
                print(f"Checking {width} {path}", flush=True)
                await page.goto(url + path)
                try:
                    await page.locator("main h1").wait_for()
                except Exception:
                    (output / "render-timeout.json").write_text(json.dumps(dict(url=page.url, text=await page.locator('body').inner_text(), errors=errors, asset_errors=asset_errors, requests=requests), indent=2))
                    raise
                if not state["public"]:
                    await page.locator("main.workspace").wait_for()
                    await page.locator(".loading").wait_for(state="hidden")
                styles = await page.evaluate("""() => {
                    const h = document.querySelector('main h1'), s = getComputedStyle(h);
                    const controls = [...document.querySelectorAll('main .button, main .inline-link, .text-button, nav a, .avatar, .auth-switch a, summary, main input:not([type=hidden]), main select, main textarea')].filter(e => e.getClientRects().length);
                    return {background:getComputedStyle(document.body).backgroundColor, font:s.fontFamily,
                        weight:s.fontWeight, overflow:document.documentElement.scrollWidth > innerWidth + 1,
                        undersized:controls.filter(e => {
                            const target = e.type === 'checkbox' ? (e.closest('label') || e) : e;
                            const rect = target.getBoundingClientRect();
                            return rect.width < 44 || rect.height < 44;
                        }).map(e => {
                            const target = e.type === 'checkbox' ? (e.closest('label') || e) : e;
                            const rect = target.getBoundingClientRect();
                            return {label:e.textContent?.trim().slice(0,60) || e.getAttribute('aria-label') || e.type,
                                width:rect.width, height:rect.height};
                        }),
                        unnamed:controls.filter(e => ['INPUT','SELECT','TEXTAREA'].includes(e.tagName) && !e.getAttribute('aria-label') && !e.labels?.length).map(e => e.type),
                        smallInputs:controls.filter(e => ['INPUT','SELECT','TEXTAREA'].includes(e.tagName) && e.type !== 'checkbox' && parseFloat(getComputedStyle(e).fontSize) < 16).length};
                }""")
                await page.wait_for_function("document.getElementById('main-content').getAnimations({subtree:true}).every(a=>a.playState!=='running')", timeout=7000)
                label = f"{theme} {width} {path}"
                check(label + " neutral canvas", styles["background"] == ("rgb(245, 245, 243)" if theme == "light" else "rgb(20, 20, 19)"), styles["background"])
                decor = await page.locator('.atmosphere').evaluate_all("els=>els.map(e=>({display:getComputedStyle(e).display,pointer:getComputedStyle(e).pointerEvents}))")
                check(label + " atmosphere scope", len(decor) == 1 and decor[0]["display"] == ("block" if state["public"] else "none") and decor[0]["pointer"] == "none", decor)
                toggle = page.get_by_role("button", name="Dark theme", exact=True)
                check(label + " theme control", await toggle.count() == 1 and await toggle.get_attribute("aria-pressed") == str(theme == "dark").lower())
                contrast_failures = await page.evaluate(CONTRAST_JS)
                check(label + " rendered text and input contrast", not contrast_failures, contrast_failures)
                headings = {"/": "Jobs and applications, in one place.", "/login": "Sign in", "/signup": "Create account", "/home": "Home", "/jobs": "Jobs", "/profile": "Profile", "/onboarding": "Set up your profile", "/applications": "Applications", "/applications/fixture-app/review": "Review application", "/interviews": "Interviews", "/resources": "Resources"}
                if path in headings:
                    check(label + " descriptive heading", " ".join((await page.locator("main h1").inner_text()).split()) == headings[path])
                copy_text = (await page.locator("main").inner_text()).lower()
                check(label + " plain copy", not any(s in copy_text for s in ["next chapter", "your story", "considered fit", "calm, organized", "a little clarity", "more thoughtful", "more intention"]))
                material = await page.locator(".site-header").evaluate("e => {const s=getComputedStyle(e);return {filter:s.backdropFilter,position:s.position,shadow:s.boxShadow,background:s.backgroundColor}}")
                check(label + " sticky frosted header", material["position"] == "sticky" and "blur(" in material["filter"] and material["background"].startswith("rgba("), material)
                if await page.locator("main .panel").count():
                    glass = await page.locator("main .panel").first.evaluate("e => {const s=getComputedStyle(e);return {filter:s.backdropFilter,background:s.backgroundColor,highlight:s.backgroundImage,shadow:s.boxShadow}}")
                    check(label + " opaque workspace card", glass["filter"] == "none" and not glass["background"].startswith("rgba(") and glass["highlight"] == "none", glass)
                opaque = await page.locator("main input:not([type=checkbox]), main select, main textarea, main .notice").evaluate_all("els => els.filter(e => getComputedStyle(e).backgroundColor.startsWith('rgba(')).map(e=>e.tagName)")
                check(label + " opaque fields and notices", not opaque, opaque)
                check(label + " sans heading", "Georgia" not in styles["font"] and "Times" not in styles["font"] and 500 <= int(styles["weight"]) <= 600, styles["font"])
                check(label + " no page overflow", not styles["overflow"])
                check(label + " named controls", not styles["unnamed"], styles["unnamed"])
                check(label + " touch targets", not styles["undersized"], styles["undersized"])
                check(label + " input text size", not styles["smallInputs"], styles["smallInputs"])
                if state["public"] and path == "/":
                    check(label + " single hero", await page.locator(".landing-hero").evaluate("e => getComputedStyle(e).gridTemplateColumns.split(' ').length === 1"))
                    check(label + " no forced line breaks", await page.locator("main h1 br").count() == 0)
                    check(label + " neutral action", await page.locator("main .primary").first.evaluate("e => getComputedStyle(e).backgroundColor") == ("rgb(26, 26, 26)" if theme == "light" else "rgb(244, 244, 239)"))
                elif path in {"/login", "/signup"}:
                    check(label + " centered auth", await page.locator(".auth-layout").evaluate("e => e.getBoundingClientRect().width <= 520 && getComputedStyle(e).gridTemplateColumns.split(' ').length === 1"))
                elif path == "/home":
                    check(label + " compact Home", await page.locator(".dashboard-hero").evaluate("e => e.getBoundingClientRect().height < 320"))
                    check(label + " chart tables", await page.locator(".chart-panel details table").count() == 2)
                    palette = await page.locator('.legend i').evaluate_all("els => els.map(e => getComputedStyle(e).backgroundColor)")
                    check(label + " status chart colors", palette == (['rgb(65, 83, 64)', 'rgb(112, 130, 106)', 'rgb(141, 143, 132)'] if theme == "light" else ['rgb(148, 178, 138)', 'rgb(112, 130, 106)', 'rgb(141, 143, 132)']), palette)
                    shapes = await page.locator('.legend i').evaluate_all("els => els.map(e => ({radius:getComputedStyle(e).borderRadius,transform:getComputedStyle(e).transform}))")
                    check(label + " non-color legend encoding", shapes[0]['radius'] != shapes[1]['radius'] and shapes[2]['transform'] != 'none', shapes)
                    check(label + " chart values", await page.locator(".donut").get_attribute("aria-label") == "2 submitted, 3 in progress, 1 cancelled")
                if path in {"/", "/login", "/home", "/jobs", "/applications/fixture-app/review"} and width in {390, 1280}:
                    name = path.strip("/").split("/")[0] or "landing"
                    if "review" in path: name = "review"
                    await page.screenshot(path=str(output / f"{name}-{theme}-{width}.png"), full_page=True)

        state["public"] = True
        await page.goto(url + "/login")
        await page.get_by_label("Email address").fill("synthetic@example.invalid")
        await page.get_by_label("Password", exact=True).fill("synthetic-password")
        await page.locator("form button").click()
        await page.locator("main [role=alert]").wait_for()
        check("auth error announced", "Synthetic sign-in rejected" in await page.locator("main [role=alert]").inner_text())
        await page.keyboard.press("Tab")
        check("keyboard focus visible", await page.evaluate("() => getComputedStyle(document.activeElement).outlineStyle !== 'none'"))
        state["public"] = False
        await page.goto(url + "/jobs")
        await page.locator(".job-card").wait_for()
        check("six navigation links", await page.get_by_role("navigation").get_by_role("link").count() == 6)
        await page.get_by_role("tab", name="For you", exact=True).click()
        await page.get_by_label("Matching method").wait_for()
        check("match controls retained", await page.get_by_role("button", name="Refresh my matches", exact=True).count() == 1)
        await page.get_by_role("tab", name="All opportunities").click()
        combo = page.get_by_role("combobox", name="Company", exact=True)
        await combo.fill("Synthetic")
        await page.get_by_role("listbox", name="Company suggestions").get_by_role("option").wait_for()
        await combo.press("ArrowDown")
        await combo.press("Enter")
        check("keyboard company selection retained", await combo.input_value() == long)
        await page.get_by_role("combobox", name="Bulk application mode", exact=True).click()
        await page.get_by_role("option", name="Automatic submission", exact=True).click()
        check("automatic mode retained", await page.get_by_role("button", name="Start automatic applications", exact=True).count() == 1)
        await page.goto(url + "/profile")
        await page.get_by_role("button", name="Save profile", exact=True).wait_for()
        check("resume consent retained", await page.get_by_role("button", name="Interpret resume with AI").is_disabled())
        await page.get_by_role("button", name="+ Add experience", exact=True).click()
        check("profile editor retained", await page.get_by_role("button", name="Remove experience").count() == 1)
        await page.goto(url + "/applications/fixture-app/review")
        submit = page.get_by_role("button", name="Approve & submit application", exact=True)
        await submit.wait_for()
        check("submission needs approval", await submit.is_disabled())
        await page.get_by_label("I have reviewed all answers and explicitly approve submitting this application.").check()
        check("approval enables explicit action", await submit.is_enabled())
        await page.get_by_text("View filled answers (1)").click()
        check("filled answer edit retained", await page.get_by_role("button", name="Edit filled answers", exact=True).is_visible())
        for scheme in ["light", "dark"]:
            await page.emulate_media(color_scheme=scheme)
            await page.evaluate("t=>localStorage.setItem('turio-theme',t)", scheme)
            for status in ["submitted", "verification_failed", "automation_failed"]:
                app["status"] = status
                await page.goto(url + "/applications/fixture-app/review")
                await page.locator('.status-' + status).wait_for()
                failures_for_state = await page.evaluate(CONTRAST_JS)
                check(f"{scheme} {status} contrast", not failures_for_state, failures_for_state)
        await page.evaluate("""() => {const e=document.createElement('p');e.className='notice';
          e.id='contrast-probe';e.textContent='Contrast checker negative control';
          document.querySelector('main').append(e);e.style.color=getComputedStyle(e).backgroundColor;}""")
        negative = await page.evaluate(CONTRAST_JS)
        check("contrast negative control rejected", any(e['label'] == 'Contrast checker negative control' and e['ratio'] < 1.1 for e in negative), negative)
        await page.locator('#contrast-probe').evaluate('e=>e.remove()')
        app["status"] = "verification_failed"
        await page.reload()
        reset = page.get_by_role("button", name="Reset to review", exact=True)
        await reset.wait_for()
        check("uncertain reset needs acknowledgement", await reset.is_disabled())
        await page.get_by_label("I checked the employer site and confirmed this application was not submitted.").check()
        check("acknowledgement enables reset", await reset.is_enabled())

        for mode in ["empty", "error", "delay"]:
            state[mode] = True
            await page.goto(url + "/jobs")
            target = page.locator(".empty") if mode == "empty" else page.locator("main [role=alert]") if mode == "error" else page.locator(".loading")
            await target.wait_for()
            check(mode + " state rendered", await target.is_visible())
            if mode == "delay": release.set()
            state[mode] = False
        release.clear()
        state["delay"] = True
        await page.goto(url + "/home")
        await page.locator(".stats").wait_for()
        check("Home progress independent of matches", await page.locator(".stats").is_visible())
        release.set()
        state["delay"] = False
        await page.goto(url + "/login")
        await page.locator("form .button").wait_for()
        motion = await page.locator("form .button").evaluate("e => {const s=getComputedStyle(e);return {properties:s.transitionProperty,durations:s.transitionDuration,easing:s.transitionTimingFunction}}")
        check("short explicit retargetable motion", 'all' not in motion['properties'] and all(.15 <= float(v.strip().rstrip('s')) <= .28 for v in motion['durations'].split(',')) and 'cubic-bezier(0.675, 0.15, 0.1, 1)' in motion['easing'], motion)
        check("no page entry animation", await page.locator("main").evaluate("e => getComputedStyle(e).animationName") == 'none')
        button = page.locator("form .button")
        await button.focus()
        await page.keyboard.down("Space")
        check("keyboard press does not move", await button.evaluate("e => getComputedStyle(e).transform") == 'none')
        await page.keyboard.up("Space")
        cdp = await context.new_cdp_session(page)
        document = await cdp.send('DOM.getDocument')
        svg = await cdp.send('DOM.querySelector', dict(nodeId=document['root']['nodeId'], selector='.atmosphere svg'))
        described = await cdp.send('DOM.describeNode', dict(nodeId=svg['nodeId']))
        ax = await cdp.send('Accessibility.getPartialAXTree', dict(backendNodeId=described['node']['backendNodeId'], fetchRelatives=False))
        check('atmosphere excluded from accessibility tree', bool(ax['nodes']) and all(n['ignored'] for n in ax['nodes']), ax['nodes'])
        for feature in ['prefers-reduced-transparency', 'prefers-contrast', 'forced-colors']:
            value = 'reduce' if feature == 'prefers-reduced-transparency' else 'more' if feature == 'prefers-contrast' else 'active'
            await cdp.send('Emulation.setEmulatedMedia', dict(features=[dict(name=feature,value=value)]))
            check(feature + " emulation active", await page.evaluate("([f,v]) => matchMedia(`(${f}: ${v})`).matches", [feature,value]))
            material = await page.locator('.site-header, .auth-card').evaluate_all("els => els.map(e => {const s=getComputedStyle(e); return {filter:s.backdropFilter,background:s.backgroundColor,image:s.backgroundImage}})")
            check(feature + " solid material fallback", all(s['filter'] == 'none' and s['image'] == 'none' and not s['background'].startswith('rgba(') for s in material), material)
            check(feature + " suppresses atmosphere", await page.locator('.atmosphere').evaluate("e=>getComputedStyle(e).display") == 'none')
        await cdp.send('Emulation.setEmulatedMedia', dict(features=[]))
        await page.reload()
        await page.locator('form .button').wait_for()
        # Exercise the shipped base styles as if the positive filter @supports branch were unavailable.
        await page.evaluate("""() => {for(const sheet of document.styleSheets) {try {for(let i=sheet.cssRules.length-1;i>=0;i--) {const r=sheet.cssRules[i]; if(r instanceof CSSSupportsRule && r.conditionText.includes('backdrop-filter')) sheet.deleteRule(i)}} catch {}}}""")
        fallback = await page.locator('.site-header, .auth-card').evaluate_all("els => els.map(e => {const s=getComputedStyle(e);return {filter:s.backdropFilter,background:s.backgroundColor}})")
        check("unsupported filter opaque fallback", all(s['filter'] == 'none' and not s['background'].startswith('rgba(') for s in fallback), fallback)
        await page.locator('.atmosphere svg').evaluate('e=>e.remove()')
        check("SVG-free gradient fallback", await page.locator('.atmosphere').evaluate("e=>getComputedStyle(e).display==='block' && getComputedStyle(e,'::before').backgroundImage!=='none'"))
        await page.reload()
        await page.emulate_media(reduced_motion="reduce")
        await page.goto(url + "/login")
        check("reduced motion freezes atmosphere", await page.locator('.atmosphere').evaluate("e=>getComputedStyle(e,'::before').animationName") == 'none')
        button = page.locator("form .button")
        await button.wait_for()
        await button.hover()
        await page.mouse.down()
        check("reduced motion removes press transform", await button.evaluate("e => getComputedStyle(e).transform") == "none")
        await page.mouse.up()
        await browser.close()
    check("all APIs intercepted", not unexpected, unexpected)
    check("no page errors", not errors, errors)
    check("static assets hydrate", not asset_errors, asset_errors)
    result = dict(passed=len(checks), failed=len(failures), checks=checks, failures=failures,
        unexpected_requests=unexpected, page_errors=errors, asset_errors=asset_errors, requests=len(requests),
        limits="Synthetic browser emulation only; no real phone/keyboard, backend or employer actions.")
    (output / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(dict(passed=len(checks), failed=len(failures), failures=failures)))
    return not failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:13002")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if asyncio.run(main(args.url.rstrip("/"), args.output)) else 1)
