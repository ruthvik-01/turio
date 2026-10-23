"""Synthetic UI contracts: all API traffic intercepted, no provider/employer writes."""
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
    profile = {'id': 'profile', 'version': 4, 'full_name': 'Synthetic Candidate', 'phone': '123',
        'location': None, 'preferred_roles': [], 'linkedin_url': None, 'github_url': None,
        'portfolio_url': None, 'work_authorization_status': None, 'sponsorship_required': None,
        'contact_email': 'contact@example.com', 'summary': 'Source-backed summary.',
        'certifications': ['Source Certificate'], 'achievements': ['Source Achievement'],
        'skills': [], 'experiences': [], 'educations': [], 'projects': []}
    resume = {'id': '11111111-1111-4111-8111-111111111111', 'checksum': 'fixture-hash', 'original_filename': 'synthetic.pdf'}
    app_id = '22222222-2222-4222-8222-222222222222'
    prefix = '/api/applications/' + app_id
    field = {'id': 'phone', 'field_key': 'phone', 'label': 'Best number to reach you', 'input_type': 'tel',
        'required': True, 'normalized_intent': 'phone', 'options': [], 'value': '123',
        'value_source': 'jev_profile', 'user_confirmed': False, 'jev_uncertain': True,
        'jev_confidence': None, 'jev_winner_probability': None}
    app = {'id': app_id, 'job': {'id': 'job', 'title': 'Synthetic Engineer', 'company': 'Synthetic Fixture', 'company_logo_url': None},
        'application_url': 'https://employer.invalid/never-opened', 'status': 'needs_input',
        'outcome': None, 'notes': None, 'resume_id': resume['id'], 'fields': [field], 'missing_fields': ['Phone'],
        'readiness_score': 0, 'events': [], 'review_token': None, 'submitted_at': None, 'submission_method': None}
    requests, unexpected, errors, checks = [], [], [], []

    async def intercept(route):
        request = route.request
        parsed = urlparse(request.url)
        if parsed.netloc != origin.netloc:
            unexpected.append('external request'); await route.abort(); return
        if not parsed.path.startswith('/api/'):
            if request.method in {'GET', 'HEAD'}: await route.continue_()
            else: unexpected.append(parsed.path); await route.abort()
            return
        body = request.post_data_json if request.post_data else None
        requests.append({'path': parsed.path, 'method': request.method, 'body': body})
        data = None
        if parsed.path == '/api/auth/me': data = {'id': 'synthetic-user', 'email': 'synthetic@example.com'}
        elif parsed.path == '/api/resumes/latest': data = resume
        elif parsed.path == '/api/profiles/me':
            if request.method == 'PATCH':
                assert body['expected_profile_version'] == profile['version']
                profile.update({k: v for k, v in body.items() if k not in {'expected_profile_version', 'skills'}})
                profile['skills'] = [{'name': n, 'normalized_name': n.lower()} for n in body['skills']]
                profile['version'] += 1
            data = profile
        elif parsed.path == f"/api/resumes/{resume['id']}/suggestions":
            assert body == {'consent': True}
            data = {'resume_id': resume['id'], 'resume_checksum': resume['checksum'], 'profile_version': profile['version'],
                'model': 'dots-studio/dots-3-note-preview:free', 'provider': 'openrouter', 'status': 'complete', 'overflow': 0, 'unresolved': 0,
                'suggestions': [{'id': 'heading', 'heading': 'Toolbox', 'excerpt': 'Toolbox\nPython, SQL', 'section': 'skills',
                    'confidence': None, 'winner_probability': None, 'uncertain': True}], 'suggested_fields': {'skills': ['Python', 'SQL'], 'certifications': ['Jev Source Certificate']}}
        elif parsed.path == prefix: data = app
        elif parsed.path == prefix + '/capability': data = {'available': True, 'reason': None}
        elif parsed.path == prefix + '/start': data = app
        elif parsed.path == prefix + '/answers':
            for answer in body['answers']:
                field['value'] = answer['value']; field['user_confirmed'] = answer['user_confirmed']
            data = app
        else:
            unexpected.append(parsed.path)
            await route.fulfill(status=404, json={'data': None, 'error': {'code': 'FIXTURE', 'message': 'Unexpected request'}})
            return
        await route.fulfill(status=200, json={'data': copy.deepcopy(data), 'error': None, 'request_id': 'synthetic'})

    async with async_playwright() as playwright:
        kwargs = {'headless': True}
        if os.environ.get('BROWSER_EXECUTABLE_PATH'): kwargs['executable_path'] = os.environ['BROWSER_EXECUTABLE_PATH']
        browser = await playwright.chromium.launch(**kwargs)
        context = await browser.new_context()
        await context.route('**/*', intercept)
        page = await context.new_page()
        page.set_default_timeout(5000)
        page.on('pageerror', lambda e: errors.append(str(e)))
        await page.goto(url + '/profile')
        suggest = page.get_by_role('button', name='Interpret resume with AI', exact=True)
        assert await suggest.is_disabled()
        assert 'No Google service is used.' in await page.locator('body').inner_text()
        assert await page.get_by_label('Application email (does not change login)', exact=True).input_value() == 'contact@example.com'
        assert await page.get_by_label('Professional summary', exact=False).input_value() == 'Source-backed summary.'
        consent = page.get_by_label('I agree to send these excerpts to the external AI service for this action.')
        await consent.check(); await suggest.click()
        await page.get_by_text('Toolbox → skills', exact=True).wait_for()
        await page.get_by_text('Uncertain suggestion: verify the source before accepting.', exact=True).wait_for()
        await page.get_by_text('Confidence/probability scores are unavailable.', exact=False).wait_for()
        assert not await consent.is_checked()
        await page.get_by_label('Skills', exact=False).fill('Go')
        assert await page.get_by_role('button', name='Use suggested changes in editor').is_disabled()
        await page.get_by_role('button', name='Discard unsaved edits').click()
        await consent.check(); await suggest.click()
        await page.get_by_text('Toolbox → skills', exact=True).wait_for()
        await page.get_by_role('button', name='Use suggested changes in editor').click()
        await page.get_by_text('Suggested changes are in the editor.', exact=False).wait_for()
        assert await page.get_by_label('Skills', exact=False).input_value() == 'Python, SQL'
        assert await page.get_by_label('Certifications', exact=False).input_value() == 'Jev Source Certificate'
        await page.get_by_role('button', name='Save profile', exact=True).click()
        await page.get_by_text('Profile saved.', exact=False).wait_for()
        assert profile['certifications'] == ['Jev Source Certificate']
        assert profile['contact_email'] == 'contact@example.com'
        checks.append('per-action consent, source evidence, supplemental merge, dirty-edit guard and versioned save')
        await consent.check(); await suggest.click()
        await page.get_by_text('Toolbox → skills', exact=True).wait_for()
        profile['version'] += 1
        await page.get_by_role('button', name='Use suggested changes in editor').click()
        await page.get_by_text('Your resume or profile changed.', exact=False).wait_for()
        checks.append('stale suggestion refused before editor merge')
        await page.goto(url + '/applications/' + app_id)
        phone = page.get_by_label('Best number to reach you', exact=False)
        confirm = page.get_by_label('I explicitly confirm this AI suggestion is accurate.')
        await confirm.wait_for()
        await page.get_by_text('Uncertain mapping', exact=False).wait_for()
        assert not await confirm.is_checked()
        await phone.fill('456')
        assert not await confirm.is_checked()
        await page.get_by_role('button', name='Save answers', exact=True).click()
        await page.get_by_text('Application updated.', exact=True).wait_for()
        assert requests[-1]['body']['answers'][0]['jev_confirmed'] is False
        await confirm.check(); await page.get_by_role('button', name='Save answers', exact=True).click()
        await page.get_by_text('Application updated.', exact=True).wait_for()
        assert requests[-1]['body']['answers'][0]['jev_confirmed'] is True
        await page.get_by_text('View filled answers', exact=False).click()
        await page.get_by_role('button', name='Edit saved answers', exact=True).click()
        await phone.fill('789'); assert not await confirm.is_checked()
        checks.append('Jev confirmation remains explicit through edits and re-edits')
        assert 'typesafe' not in (await page.locator('body').inner_text()).lower()
        ai = page.get_by_label('Use AI to suggest unfamiliar field mappings for this action.')
        apply = page.get_by_role('button', name='Apply with Agent', exact=True)
        previous = len(requests)
        page.once('dialog', lambda dialog: dialog.dismiss())
        await apply.click()
        assert len(requests) == previous, 'Declined permission must not start preparation'
        await ai.check()
        async def approve_browser(dialog):
            assert 'Allow Turio' in dialog.message and 'submit' in dialog.message
            await dialog.accept()
        page.once('dialog', approve_browser)
        await apply.click()
        await page.get_by_text('Application updated.', exact=True).wait_for()
        assert requests[-1]['body']['ai_assist'] is True and not await ai.is_checked()
        checks.append('browser permission decline/accept and per-action AI consent reset')
        assert not unexpected and not errors, (unexpected, errors)
        output.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(output/'confirmation.png'), full_page=True)
        result = {'passed': len(checks), 'checks': checks, 'intercepted_requests': len(requests), 'page_errors': errors,
            'unexpected_requests': unexpected, 'limitations': 'Synthetic frontend contracts only; no provider/employer/backend writes.'}
        (output/'verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        for check in checks: print('PASS:', check)
        await browser.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:13001')
    parser.add_argument('--output', type=Path, default=Path('.runtime/jev/ui'))
    args = parser.parse_args()
    asyncio.run(main(args.url.rstrip('/'), args.output))
