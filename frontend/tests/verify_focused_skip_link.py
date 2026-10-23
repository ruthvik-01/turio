"""Catch sticky-header stacking that obscures the first keyboard navigation link."""
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
    rows, unexpected, errors = [], [], []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(service_workers='block')
        async def intercept(route):
            parsed = urlparse(route.request.url)
            if parsed.netloc != origin.netloc or route.request.method != 'GET':
                unexpected.append(route.request.url)
                await route.abort()
            elif parsed.path == '/api/auth/me':
                await route.fulfill(status=401, json={'data': None, 'error': {'code': 'UNAUTHORIZED', 'message': 'Synthetic signed-out session'}})
            elif parsed.path.startswith('/api/'):
                unexpected.append(parsed.path)
                await route.abort()
            else:
                await route.continue_()
        await context.route('**/*', intercept)
        page = await context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        for width in [390, 768, 1280]:
            await page.set_viewport_size({'width': width, 'height': 900})
            await page.goto(url + '/login')
            await page.locator('main h1').wait_for()
            await page.keyboard.press('Tab')
            row = await page.locator('.skip-link').evaluate('''e => {
                const r = e.getBoundingClientRect();
                const hit = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
                return {focused:e === document.activeElement, inViewport:r.top >= 0 && r.bottom <= innerHeight,
                    unobscured:e.contains(hit), hit:hit?.tagName};
            }''')
            row['width'] = width
            rows.append(row)
            await page.screenshot(path=str(output / f'skip-link-{width}.png'))
        await browser.close()
    failed = sum(not (r['focused'] and r['inViewport'] and r['unobscured']) for r in rows)
    result = {'passed': len(rows) - failed, 'failed': failed, 'checks': rows, 'unexpected_requests': unexpected, 'page_errors': errors}
    (output / 'results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))
    return not failed and not unexpected and not errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if asyncio.run(main(args.url.rstrip('/'), args.output)) else 1)
