"""Synthetic bulk-mode browser contracts; every API/employer request intercepted."""
import argparse
import asyncio
import copy
import json
import os
from pathlib import Path
from urllib.parse import urlparse


async def main(url, output):
    from playwright.async_api import async_playwright
    origin = urlparse(url)
    if origin.hostname not in {'localhost', '127.0.0.1'} or origin.scheme != 'http':
        raise ValueError('Loopback frontend required')
    jobs = [{'id': f'job-{i}', 'title': f'Engineer {i}', 'company': f'Synthetic Company {i}', 'location': 'Test City',
        'description': 'Synthetic role', 'job_url': 'https://employer.invalid/job', 'application_url': 'https://employer.invalid/job',
        'ats': 'ashby', 'required_skills': []} for i in range(1, 5)]
    apps, requests, unexpected, errors, checks = {}, [], [], [], []
    fail_submit = False
    hold_review = False
    review_started, release_review = asyncio.Event(), asyncio.Event()

    def application(i):
        return {'id': f'bulk-{i}', 'job': jobs[i - 1], 'application_url': 'https://employer.invalid/job', 'status': 'created',
            'resume_id': 'synthetic-resume', 'profile_version': 3, 'manual_submission_required': i == 3,
            'outcome': None, 'notes': None, 'review_token': None, 'events': [], 'readiness_score': 1,
            'submitted_at': None, 'submission_method': None, 'missing_fields': [],
            'fields': [{'id': f'name-{i}', 'field_key': 'name', 'label': 'Full name', 'input_type': 'text', 'required': True,
                'options': [], 'value': 'Synthetic Candidate', 'value_source': 'profile', 'user_confirmed': True}]}

    async def intercept(route):
        req = route.request
        parsed = urlparse(req.url)
        if parsed.netloc != origin.netloc:
            unexpected.append('external request'); await route.abort(); return
        path = parsed.path
        if not path.startswith('/api/'):
            if req.method in {'GET', 'HEAD'}: await route.continue_()
            else: unexpected.append(path); await route.abort()
            return
        body = req.post_data_json if req.post_data else None
        requests.append({'path': path, 'method': req.method, 'body': body, 'key': req.headers.get('idempotency-key')})
        data, status, error = None, 200, None
        if path == '/api/auth/me': data = {'id': 'fixture-user', 'email': 'synthetic@example.com'}
        elif path == '/api/jobs': data = {'jobs': jobs, 'total': 4, 'limit': 12, 'offset': 0}
        elif path == '/api/jobs/companies': data = []
        elif path == '/api/applications' and req.method == 'POST':
            i = int(body['job_id'].split('-')[-1]); apps.setdefault(i, application(i)); data = apps[i]
            assert body['reuse_existing'] is True
        elif path.startswith('/api/applications/bulk-'):
            parts = path.split('/'); i = int(parts[3].split('-')[-1]); action = parts[4] if len(parts) > 4 else ''
            if not action and req.method == 'GET': data = apps[i]
            elif action == 'capability': data = {'available': True, 'reason': None}
            elif action == 'start':
                apps[i]['status'] = 'needs_input' if i == 4 else 'ready_for_review'
                if i == 4:
                    apps[i]['fields'][0].update(value_source='ai_profile', user_confirmed=False)
                    apps[i]['missing_fields'] = ['Full name']
                data = apps[i]
            elif action == 'review':
                assert i in (1, 2), 'Manual or unconfirmed job reached automatic review'
                if hold_review and i == 1:
                    review_started.set(); await release_review.wait()
                apps[i]['review_token'] = 'a' * 64; data = apps[i]
            elif action == 'approve-submit':
                assert body == {'approved': True, 'review_token': 'a' * 64}
                assert req.headers.get('idempotency-key')
                if fail_submit:
                    apps[i]['status'] = 'submitting'
                    status, error = 503, {'code': 'FIXTURE', 'message': 'Synthetic uncertain submission'}
                else:
                    apps[i].update(status='submitted', submission_method='agent')
                    data = apps[i]
            else: unexpected.append(path); await route.abort(); return
        else: unexpected.append(path); await route.abort(); return
        await route.fulfill(status=status, json={'data': copy.deepcopy(data), 'error': error})

    async with async_playwright() as driver:
        browser = await driver.chromium.launch(headless=True, executable_path=os.environ.get('BROWSER_EXECUTABLE_PATH'))
        context = await browser.new_context(service_workers='block', viewport={'width': 1440, 'height': 1000})
        await context.route('**/*', intercept)
        page = await context.new_page(); page.set_default_timeout(10000)
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('dialog', lambda d: asyncio.create_task(d.accept()))
        output.mkdir(parents=True, exist_ok=True)
        consent = page.get_by_label('I explicitly approve submitting the eligible applications shown above', exact=False)
        submit = page.get_by_role('button', name='Approve & submit ready applications', exact=True)

        async def prepare(ai=False):
            await page.goto(url + '/jobs')
            await page.get_by_role('button', name='Select visible jobs', exact=True).click()
            if ai: await page.get_by_label('Use AI for unfamiliar employer fields', exact=False).check()
            await page.get_by_role('button', name='Prepare selected applications', exact=True).click()
            await page.get_by_text('Bulk preparation complete.', exact=False).wait_for()

        async def automatic(hold=True):
            await page.get_by_label('Bulk application mode', exact=False).select_option('automatic')
            if hold: await page.get_by_label('Hold Engineer 2 at Synthetic Company 2 for review', exact=True).check()
            assert await submit.is_disabled()
            await consent.check()
            assert await submit.is_enabled()

        try:
            await prepare(ai=True)
            assert await page.get_by_label('Bulk application mode', exact=False).input_value() == 'review'
            assert not [r for r in requests if r['path'].endswith(('/review', '/approve-submit'))]
            assert all(r['body']['ai_assist'] is True for r in requests if r['path'].endswith('/start'))
            assert not await page.get_by_label('Use AI for unfamiliar employer fields', exact=False).is_checked()
            await page.get_by_text('View filled fields for Engineer 2 at Synthetic Company 2', exact=True).click()
            row = page.locator('.review-box').filter(has=page.get_by_text('Synthetic Company 2 · Engineer 2', exact=True))
            await row.get_by_text('Synthetic Candidate', exact=True).wait_for()
            checks.append('default review mode, per-job field preview and explicit per-batch AI consent reset')
            await automatic()
            await submit.click()
            await page.get_by_text('Automatic batch finished.', exact=False).wait_for()
            sent = [r for r in requests if r['path'].endswith('/approve-submit')]
            assert [r['path'] for r in sent] == ['/api/applications/bulk-1/approve-submit']
            assert apps[1]['status'] == 'submitted' and apps[2]['status'] == 'ready_for_review'
            assert apps[3]['status'] == 'ready_for_review' and apps[4]['status'] == 'needs_input'
            assert await submit.is_disabled()
            checks.append('one explicit batch approval, held/manual/unconfirmed skips and no duplicate submit')
            await page.set_viewport_size({'width': 390, 'height': 844})
            assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
            await page.screenshot(path=str(output/'bulk-mobile.png'), full_page=True)
            await page.set_viewport_size({'width': 1440, 'height': 1000})

            for changed in ('answers', 'job'):
                apps.clear(); start = len(requests)
                await prepare(); await automatic()
                if changed == 'answers': apps[1]['fields'][0]['value'] = 'Changed Synthetic Candidate'
                else: apps[1]['job'] = {**apps[1]['job'], 'title': 'Changed synthetic role'}
                await submit.click()
                await page.get_by_text('Prepared job or answers changed.', exact=False).wait_for()
                assert not [r for r in requests[start:] if r['path'].endswith('/approve-submit')]
            checks.append('changed prepared values or job identity refused before review or submission')

            apps.clear(); start = len(requests); fail_submit = True
            await prepare(); await automatic(); await submit.click()
            await page.get_by_text('Synthetic uncertain submission', exact=False).wait_for()
            assert len([r for r in requests[start:] if r['path'].endswith('/approve-submit')]) == 1
            assert await page.get_by_role('button', name='Retry failed applications', exact=True).count() == 0
            assert await submit.is_disabled() and apps[1]['status'] == 'submitting'
            checks.append('uncertain submission remains pending without an automatic retry')

            apps.clear(); start = len(requests); fail_submit = False; hold_review = True
            review_started, release_review = asyncio.Event(), asyncio.Event()
            await prepare(); await automatic(hold=False); await submit.click()
            await asyncio.wait_for(review_started.wait(), 5)
            await page.evaluate('''() => { const original = Date.now; Date.now = () => original() + 15 * 60 * 1000 + 1000; }''')
            release_review.set()
            await page.get_by_text('Bulk approval expired.', exact=False).last.wait_for()
            assert not [r for r in requests[start:] if r['path'].endswith('/approve-submit')]
            checks.append('expired batch approval refused before final submission')

            apps.clear(); start = len(requests)
            review_started, release_review = asyncio.Event(), asyncio.Event()
            await prepare(); await automatic(hold=False); await submit.click()
            await asyncio.wait_for(review_started.wait(), 5)
            await page.get_by_role('button', name='Stop after current job', exact=True).click()
            release_review.set()
            await page.get_by_text('Stopped after the current job.', exact=False).wait_for()
            assert [r['path'] for r in requests[start:] if r['path'].endswith('/approve-submit')] == ['/api/applications/bulk-1/approve-submit']
            assert apps[2]['status'] == 'ready_for_review'
            checks.append('stop finishes only the already approved current job')
            assert not unexpected and not errors, (unexpected, errors)
        finally:
            release_review.set()
            await browser.close()
        result = {'passed': len(checks), 'checks': checks, 'requests': len(requests), 'unexpected_requests': unexpected,
            'page_errors': errors, 'limitations': 'Intercepted synthetic UI only; no actual employer/backend submissions.'}
        (output/'verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:13000')
    parser.add_argument('--output', type=Path, default=Path('.runtime/bulk-modes/ui'))
    args = parser.parse_args()
    asyncio.run(main(args.url.rstrip('/'), args.output))
