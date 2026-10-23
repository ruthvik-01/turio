"""Synthetic UI checks; every API request intercepted, no real submissions."""
import argparse
import asyncio
import copy
import json
from pathlib import Path
from urllib.parse import urlparse


async def main(url, output):
    from playwright.async_api import async_playwright
    origin = urlparse(url)
    assert origin.hostname in {'127.0.0.1', 'localhost'}
    question = 'Are you currently based in the EU or UK and eligible to work here?'
    jobs = [dict(id=f'job-{i}', title=f'Role {i}', company='Synthetic Company', location='Test',
                 ats='ashby', description='Fixture', job_url='https://employer.invalid',
                 application_url='https://employer.invalid', required_skills=[]) for i in range(1, 4)]
    apps, requests, unexpected, errors, checks, failures = {}, [], [], [], [], []
    release_matches = asyncio.Event()
    current_profile_version = 1
    fail_profile = False
    def app(job):
        return dict(id='app-' + job['id'], job=job, status='created', application_url=job['application_url'],
                    resume_id='owned-resume', profile_version=1, manual_submission_required=False,
                    notes=None, outcome=None, submitted_at=None, submission_method=None,
                    review_token=None, events=[], readiness_score=0, missing_fields=[question],
                    fields=[dict(id='q-' + job['id'], field_key='eligibility', label=question,
                                 input_type='text', required=True, normalized_intent='custom', options=[],
                                 value=None, value_source='missing', user_confirmed=False)])
    async def intercept(route):
        req = route.request
        parsed = urlparse(req.url)
        if parsed.netloc != origin.netloc:
            unexpected.append('external'); await route.abort(); return
        path = parsed.path
        if not path.startswith('/api/'):
            await route.continue_(); return
        body = req.post_data_json if req.post_data else None
        requests.append(dict(path=path, method=req.method, body=body))
        data = None
        if path == '/api/auth/me': data = dict(id='fixture-user', email='synthetic@example.invalid')
        elif path == '/api/profiles/me':
            if fail_profile:
                await route.fulfill(status=503, json=dict(data=None, error=dict(code='FIXTURE', message='Synthetic profile unavailable')))
                return
            data = dict(full_name='Synthetic Candidate', skills=[], version=current_profile_version)
        elif path == '/api/applications/summary':
            data = dict(total=0, submitted=0, in_progress=0, cancelled=0, interviews=0, offers=0, days=[])
        elif path == '/api/matches':
            await release_matches.wait()
            data = dict(matches=[], total=0, stale=False, limit=3, offset=0)
        elif path == '/api/jobs': data = dict(jobs=jobs, total=len(jobs), limit=12, offset=0)
        elif path == '/api/jobs/companies': data = []
        elif path == '/api/applications' and req.method == 'POST':
            job = next(j for j in jobs if j['id'] == body['job_id'])
            apps.setdefault(job['id'], app(job)); data = apps[job['id']]
        elif path.startswith('/api/applications/'):
            key = path.split('/')[3].removeprefix('app-')
            current = apps[key]
            if path.endswith('/capability'): data = dict(available=True, reason=None)
            elif path.endswith('/start'):
                current.update(status='ready_for_review' if current['fields'][0]['user_confirmed'] else 'needs_input', profile_version=current_profile_version)
                data = current
            elif path.endswith('/answers'):
                assert len(body['answers']) == 1
                value = body['answers'][0]['value']
                assert body['answers'][0]['user_confirmed'] is True
                for pending in apps.values():
                    pending['fields'][0].update(value=value, value_source='saved_answer', user_confirmed=True)
                    pending.update(status='ready_for_review', missing_fields=[], readiness_score=1, review_token=None)
                data = current
            elif path.endswith('/review'):
                assert current['fields'][0]['value'] == 'No' and current['fields'][0]['user_confirmed']
                current['review_token'] = 'a' * 64; data = current
            elif path.endswith('/approve-submit'):
                assert body == dict(approved=True, review_token='a' * 64)
                assert req.headers.get('idempotency-key')
                current.update(status='submitted', submission_method='agent'); data = current
            elif req.method == 'GET': data = current
            else: unexpected.append(path); await route.abort(); return
        else: unexpected.append(path); await route.abort(); return
        await route.fulfill(json=dict(data=copy.deepcopy(data), error=None))

    async with async_playwright() as driver:
        browser = await driver.chromium.launch(headless=True)
        context = await browser.new_context(service_workers='block', viewport=dict(width=1300, height=950))
        await context.route('**/*', intercept)
        page = await context.new_page()
        page.set_default_timeout(8000)
        page.on('dialog', lambda d: asyncio.create_task(d.accept()))
        page.on('pageerror', lambda e: errors.append(str(e)))
        try:
            await page.goto(url + '/home')
            await page.get_by_role('link', name='Browse jobs', exact=False).wait_for(timeout=1500)
            assert not release_matches.is_set()
            checks.append('Home renders profile/progress while recommendations are pending')
        except Exception as exc: failures.append('Home: ' + type(exc).__name__)
        finally: release_matches.set()
        try:
            await page.goto(url + '/jobs')
            await page.get_by_role('button', name='Select visible jobs', exact=True).click()
            await page.get_by_label('Bulk application mode').select_option('automatic')
            await page.get_by_role('button', name='Start automatic applications', exact=True).click()
            await page.get_by_text('Automatic batch finished.', exact=False).wait_for()
            assert not any(r['path'].endswith('/approve-submit') for r in requests)
            shared = page.get_by_label(question, exact=False)
            assert await shared.count() == 1
            await shared.fill('No')
            await page.get_by_role('button', name='Save shared answers', exact=True).click()
            await page.get_by_text('Shared answers saved', exact=False).wait_for()
            assert len([r for r in requests if r['path'].endswith('/answers')]) == 1
            assert all(a['status'] == 'ready_for_review' for a in apps.values())
            checks.append('One input/save updates all three prepared identical questions')
            current_profile_version = 2
            await page.get_by_role('button', name='Start automatic applications', exact=True).click()
            await page.get_by_text('Automatic batch finished.', exact=False).wait_for()
            sent = [r for r in requests if r['path'].endswith('/approve-submit')]
            assert len(sent) == 3 and all(a['status'] == 'submitted' for a in apps.values())
            assert all(a['profile_version'] == 2 for a in apps.values())
            checks.append('Automatic refreshes stale-profile drafts before reviewing or sending')
            checks.append('Automatic start reviews/submits confirmed jobs without a second approval step')
            await page.get_by_role('button', name='Start automatic applications', exact=True).click()
            assert len([r for r in requests if r['path'].endswith('/approve-submit')]) == 3
            checks.append('Submitted jobs are never replayed')
            await page.goto(url + '/jobs')
            await page.get_by_role('button', name='Select visible jobs', exact=True).click()
            await page.get_by_label('Bulk application mode').select_option('automatic')
            fail_profile = True
            await page.get_by_role('button', name='Start automatic applications', exact=True).click()
            await page.get_by_role('alert').filter(has_text='Synthetic profile unavailable').wait_for()
            assert len([r for r in requests if r['path'].endswith('/approve-submit')]) == 3
            checks.append('Profile-read failure is visible and stops the automatic run')
        except Exception as exc: failures.append('Batch: ' + type(exc).__name__ + ': ' + str(exc)[:160])
        output.parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(output.with_suffix('.png')), full_page=True)
        await browser.close()
    result = dict(checks=checks, failures=failures, unexpected=unexpected, page_errors=errors, requests=len(requests))
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result), flush=True)
    assert not failures and not unexpected and not errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:13000')
    parser.add_argument('--output', type=Path, default=Path('.runtime/hosted-auto/workflow-ui.json'))
    args = parser.parse_args()
    asyncio.run(main(args.url.rstrip('/'), args.output))
