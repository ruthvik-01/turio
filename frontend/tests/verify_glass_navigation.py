"""Catch glass-card popup interception and sticky-header skip destination overlap."""
import argparse
import asyncio
import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright


async def main(url, output):
    origin = urlparse(url)
    assert origin.hostname in {'127.0.0.1', 'localhost'}
    output.mkdir(parents=True, exist_ok=True)
    rows, unexpected, errors, requests = [], [], [], []
    companies = [{'company': f'Synthetic Company {i:02d}', 'slug': f'synthetic-{i}'} for i in range(1, 7)]
    job = {'id': 'fixture-job', 'title': 'Synthetic engineering role ' * 12,
        'company': 'Synthetic long company ' * 8, 'location': 'Synthetic City',
        'description': 'Synthetic source-backed description', 'ats': 'ashby',
        'required_skills': ['Python'], 'company_logo_url': None,
        'job_url': 'https://employer.invalid/job', 'application_url': 'https://employer.invalid/job'}
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(service_workers='block')
        async def intercept(route):
            parsed = urlparse(route.request.url)
            if parsed.netloc != origin.netloc or route.request.method != 'GET':
                unexpected.append(route.request.url)
                await route.abort()
            elif parsed.path.startswith('/api/'):
                requests.append(parsed.path)
                if parsed.path == '/api/auth/me':
                    data = {'id': 'fixture-user', 'email': 'synthetic@example.invalid'}
                elif parsed.path == '/api/jobs':
                    data = {'jobs': [job], 'total': 1, 'offset': 0, 'limit': 12}
                elif parsed.path == '/api/jobs/companies':
                    data = {'companies': companies, 'total': len(companies)}
                else:
                    unexpected.append(parsed.path)
                    await route.abort()
                    return
                await route.fulfill(json={'data': data, 'error': None})
            else:
                await route.continue_()
        await context.route('**/*', intercept)
        page = await context.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        for width in [390, 768, 1280]:
            await page.set_viewport_size({'width': width, 'height': 900})
            await page.goto(url + '/jobs')
            await page.locator('.job-card').wait_for()
            crowded = await page.locator('.site-header nav a').evaluate_all('''els => els.map(e => {
                const range = document.createRange(); range.selectNodeContents(e);
                const text = range.getBoundingClientRect(), box = e.getBoundingClientRect(), s = getComputedStyle(e);
                return {label:e.textContent, textWidth:text.width,
                    available:box.width-parseFloat(s.paddingLeft)-parseFloat(s.paddingRight), shrink:s.flexShrink};
            }).filter(e => e.textWidth > e.available + 1)''')
            rows.append({'check': 'navigation labels fit click targets', 'width': width,
                'passed': not crowded, 'crowded': crowded})
            await page.keyboard.press('Tab')
            focused = await page.locator('.skip-link').evaluate('e => e === document.activeElement')
            await page.keyboard.press('Enter')
            destination = await page.evaluate('''() => {
                const h = document.querySelector('main h1').getBoundingClientRect();
                const header = document.querySelector('.site-header').getBoundingClientRect();
                return {hash:location.hash, headingTop:h.top, headerBottom:header.bottom,
                    scrollY, longPage:document.documentElement.scrollHeight > innerHeight};
            }''')
            rows.append({'check': 'skip destination clear of sticky header', 'width': width,
                'passed': focused and destination['hash'] == '#main-content' and destination['longPage'] and destination['headingTop'] >= destination['headerBottom'], **destination})
            await page.screenshot(path=str(output / f'skip-destination-{width}.png'))
            combo = page.get_by_role('combobox', name='Company', exact=True)
            await combo.fill('Synthetic')
            option = page.get_by_role('option', name='Synthetic Company 02 synthetic-2', exact=True)
            await option.wait_for()
            await option.scroll_into_view_if_needed()
            hit = await option.evaluate('''e => {
                const r = e.getBoundingClientRect(), hit = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
                const bulk = [...document.querySelectorAll('section.panel')].find(e => e.querySelector('h2')?.textContent === 'Bulk job applications')?.getBoundingClientRect();
                return {unobscured:e.contains(hit), hit:hit?.tagName, hitText:hit?.textContent?.slice(0,80),
                    x:r.x + r.width/2, y:r.y + r.height/2, bulkTop:bulk?.top,
                    filterZ:getComputedStyle(document.querySelector('.filters.panel')).zIndex};
            }''')
            await page.screenshot(path=str(output / f'company-popup-{width}.png'))
            # Raw pointer click, not locator auto-wait, forced click or keyboard selection.
            await page.mouse.click(hit['x'], hit['y'])
            selected = await combo.input_value() == 'Synthetic Company 02'
            rows.append({'check': 'company option pointer selection', 'width': width,
                'passed': hit['unobscured'] and selected, 'selected': selected, **hit})
            toggle = page.get_by_role('button', name='Dark theme', exact=True)
            dark = await toggle.get_attribute('aria-pressed') == 'true'
            box = await toggle.bounding_box()
            await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
            theme = 'light' if dark else 'dark'
            rows.append({'check': 'theme toggle real pointer', 'width': width,
                'passed': await page.locator('html').get_attribute('data-theme') == theme})
            link = page.get_by_role('navigation', name='Main navigation').get_by_role('link', name='Resources', exact=True)
            await link.scroll_into_view_if_needed()
            box = await link.bounding_box()
            await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
            await page.wait_for_url('**/resources')
            await page.get_by_role('heading', name='Resources', exact=True).wait_for()
            rows.append({'check': 'header client navigation retains theme', 'width': width,
                'passed': await page.locator('html').get_attribute('data-theme') == theme
                    and await link.get_attribute('aria-current') == 'page'})
        await browser.close()
    failed = sum(not r['passed'] for r in rows)
    result = {'passed': len(rows)-failed, 'failed': failed, 'checks': rows,
        'unexpected_requests': unexpected, 'page_errors': errors, 'requests': requests}
    (output / 'results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))
    return not failed and not unexpected and not errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if asyncio.run(main(args.url.rstrip('/'), args.output)) else 1)
