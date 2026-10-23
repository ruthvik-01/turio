"""Focused reference-fidelity regression; local public UI, no real auth/model/employer calls."""
import argparse
import asyncio
import hashlib
import json
from urllib.parse import urlparse
from playwright.async_api import async_playwright


async def main(url):
    origin = urlparse(url)
    assert origin.hostname in {"127.0.0.1", "localhost"}
    checks, failures = [], []

    def check(name, value):
        if value: checks.append(name)
        else: failures.append(name)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        state = {"signed_in": False}
        async def intercept(route):
            parsed = urlparse(route.request.url)
            if parsed.netloc != origin.netloc:
                await route.abort()
            elif parsed.path == '/api/auth/me' and state['signed_in']:
                await route.fulfill(json={'data': {'id': 'fixture-race-user', 'email': 'race@example.invalid'}, 'error': None})
            elif parsed.path.startswith("/api/"):
                status = 401 if parsed.path.startswith('/api/auth/') else 404
                await route.fulfill(status=status, json={"data": None, "error": {"code": "UNAUTHORIZED", "message": "Public UI fixture"}})
            else:
                await route.continue_()
        await context.route("**/*", intercept)
        page = await context.new_page()
        await page.bring_to_front()
        await page.goto(url + "/")
        await page.locator("main h1").wait_for()
        check("text-only Turio wordmark", (await page.locator('.brand').inner_text()).strip() == 'Turio' and await page.locator('.brand img').count() == 0)
        check("header sign in link", await page.locator('header a[href="/login"]').count() == 1)
        check("single login entry", await page.locator('a[href="/login"]').count() == 1)
        check("single signup entry", await page.locator('a[href="/signup"]').count() == 1)
        brand = await page.locator('.brand').bounding_box()
        toggle = await page.locator('.site-header .theme-toggle').bounding_box()
        check("centered public wordmark", abs(brand['x'] + brand['width']/2 - 640) < 2)
        check("theme toggle left of brand", toggle['x'] < brand['x'])
        await page.wait_for_timeout(1600)
        field = page.locator('.atmosphere canvas')
        await field.wait_for(state='visible')
        check("real WebGL field", await field.evaluate("e=>!!e.getContext('webgl2')") )
        first = hashlib.sha256(await field.screenshot()).hexdigest()
        await page.wait_for_timeout(450)
        check("field actually changes", hashlib.sha256(await field.screenshot()).hexdigest() != first)
        check("normalized finite pigment", await field.evaluate("e=>{const g=e.getContext('webgl2'),p=g.getParameter(g.CURRENT_PROGRAM);return ['uSage','uStone','uLift'].every(n=>[...g.getUniform(p,g.getUniformLocation(p,n))].every(v=>Number.isFinite(v)&&v>=0&&v<=1))}"))
        primary = page.locator('main a[href="/signup"]')
        check("hover copy clipped at rest", await primary.locator('.button-label').evaluate("e=>getComputedStyle(e).overflow==='hidden'"))
        check("reference hover easing", await primary.evaluate("e=>getComputedStyle(e).transitionTimingFunction.split(/, (?=[a-z])/).every(v=>v==='cubic-bezier(0.675, 0.15, 0.1, 1)')"))
        await primary.hover()
        await page.wait_for_timeout(160)
        check("rolling hover label", await primary.locator('.button-label-track').evaluate("e=>getComputedStyle(e).transform") != 'none')
        await page.evaluate("""() => {window.__navigationMotion=[];window.__animate=Element.prototype.animate;
          Element.prototype.animate=function(frames,options){const a=window.__animate.call(this,frames,options);
          window.__navigationMotion.push({id:this.id,duration:a.effect.getTiming().duration,easing:a.effect.getTiming().easing,frames:a.effect.getKeyframes()});return a;};}""")
        await page.locator('header a[href="/login"]').click()
        await page.wait_for_url('**/login')
        await page.locator('main h1').wait_for()
        await page.wait_for_function("window.__navigationMotion.some(a=>a.frames.some(f=>'clipPath' in f))", timeout=7000)
        animations = await page.evaluate("window.__navigationMotion")
        await page.evaluate("() => {Element.prototype.animate=window.__animate;}")
        check("real route reveal", any(a['duration'] >= 980 for a in animations))
        check("surface clip transition", any(a['id'] == 'main-content' and a['duration'] == 1200 and any('clipPath' in f for f in a['frames']) for a in animations))
        check("reference exit timing", any(a['id'] == 'main-content' and a['duration'] == 280 for a in animations))
        check("native reference easing", all(a['easing'] == 'cubic-bezier(0.675, 0.15, 0.1, 1)' for a in animations))
        await page.wait_for_timeout(1600)
        await page.get_by_role('link', name='Create an account', exact=True).click()
        await page.evaluate('history.back()')
        await page.wait_for_url(url + '/')
        await page.wait_for_timeout(700)
        check("Back wins over cancelled exit", page.url.rstrip('/') == url)
        await page.goto(url + '/login')
        await page.wait_for_timeout(1500)
        await page.get_by_label('Email address', exact=True).fill('race@example.invalid')
        await page.get_by_label('Password', exact=True).fill('synthetic-race-password')
        async def complete_auth(route):
            await asyncio.sleep(.12)
            state['signed_in'] = True
            await route.fulfill(json={'data': {'user': {'id': 'fixture-race-user', 'email': 'race@example.invalid'}}, 'error': None})
        await page.route('**/api/auth/login', complete_auth)
        await page.evaluate("() => {document.querySelector('form button[type=submit]').click();document.querySelector('.auth-switch a').click();}")
        try:
            await page.wait_for_url(url + '/home', timeout=7000)
        except Exception:
            pass
        await page.wait_for_timeout(400)
        check('auth navigation wins cancelled exit', page.url.split('?')[0] == url + '/home')
        await page.unroute('**/api/auth/login', complete_auth)
        state['signed_in'] = False
        await page.goto(url + '/')
        await page.wait_for_timeout(1500)
        await page.emulate_media(reduced_motion='reduce')
        await page.locator('main').evaluate("e=>{const a=document.createElement('article');a.className='job-card';a.id='late-motion-probe';a.textContent='Async content fixture';e.append(a)}")
        await page.wait_for_timeout(100)
        check("live reduced motion blocks new content animations", await page.locator('#late-motion-probe').evaluate("e=>e.getAnimations().every(a=>a.playState!=='running')"))
        await page.locator('#late-motion-probe').evaluate('e=>e.remove()')
        await page.goto(url + '/')
        await page.locator('main h1').wait_for()
        await page.wait_for_timeout(250)
        check("reduced motion stays readable", await page.locator('#main-content').evaluate("e=>getComputedStyle(e).opacity") == '1')
        a = hashlib.sha256(await page.locator('.atmosphere canvas').screenshot()).hexdigest()
        await page.wait_for_timeout(450)
        check("reduced motion freezes field", hashlib.sha256(await page.locator('.atmosphere canvas').screenshot()).hexdigest() == a)
        cdp = await context.new_cdp_session(page)
        await cdp.send('Emulation.setEmulatedMedia', dict(features=[dict(name='prefers-reduced-motion',value='no-preference')]))
        await page.wait_for_timeout(200)
        await cdp.send('Emulation.setEmulatedMedia', dict(features=[dict(name='prefers-contrast',value='more'),dict(name='prefers-reduced-motion',value='no-preference')]))
        await page.wait_for_timeout(120)
        timer = "e=>{const g=e.getContext('webgl2');return g.getUniform(g.getParameter(g.CURRENT_PROGRAM),g.getUniformLocation(g.getParameter(g.CURRENT_PROGRAM),'uTime'))}"
        before = await page.locator('.volume-field').evaluate(timer)
        await page.wait_for_timeout(350)
        check("suppressed field stops GPU clock", await page.locator('.volume-field').evaluate(timer) == before)
        await cdp.send('Emulation.setEmulatedMedia', dict(features=[]))
        await page.set_viewport_size({'width':390,'height':844})
        await page.wait_for_timeout(1400)
        sizes = await page.locator('.landing .actions > .button').evaluate_all('els=>els.map(e=>({width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height}))')
        check('compact mobile reference actions', len(sizes)==2 and all(e['width']<=180 and e['height']>=44 for e in sizes))
        await browser.close()
    print(json.dumps({"passed": len(checks), "failed": len(failures), "checks": checks, "failures": failures}))
    return not failures


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:13002')
    raise SystemExit(0 if asyncio.run(main(parser.parse_args().url.rstrip('/'))) else 1)
