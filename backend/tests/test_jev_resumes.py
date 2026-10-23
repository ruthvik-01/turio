import pytest

from app.services import resume_suggestions
from app.adapters import jev
from support import auth_headers, upload_resume


def test_candidates_have_stable_local_spans_and_exclusions():
    text = 'Candidate\n\nToolbox\nPython, SQL\n\nSkills\nGo\n\n- Bullet\n\nhttps://example.com\n\n2020 - 2024\n\na@example.com\n'
    candidates, overflow = resume_suggestions.heading_candidates(text, 'checksum')
    heading = next(c for c in candidates if c['heading'] == 'Toolbox')
    assert text[heading['start']:heading['end']] == heading['heading']
    assert text[heading['context_start']:heading['context_end']] == heading['excerpt']
    assert heading['id'] == next(c for c in resume_suggestions.heading_candidates(text, 'checksum')[0] if c['heading'] == 'Toolbox')['id']
    assert not any(c['heading'] in {'Skills', '- Bullet', '2020 - 2024', 'a@example.com', 'https://example.com'} for c in candidates)
    assert overflow == 0


def test_heading_overflow_is_reported():
    text = '\n\n'.join(f'Unusual Heading {i}\ncontent, python' for i in range(45))
    candidates, overflow = resume_suggestions.heading_candidates(text, 'checksum')
    assert len(candidates) == 40
    assert overflow == 5


def test_inline_values_and_skill_lists_are_not_heading_candidates():
    text = 'SKILLS\n\nCloud Computing: AWS, Azure\n\nPython, SQL\n\nOperating Systems: Linux\n'
    candidates, _ = resume_suggestions.heading_candidates(text, 'checksum')
    assert candidates == []


def test_identity_line_next_to_contact_details_is_not_a_heading():
    text = 'Avery Example\navery@example.com | +1 555 010 1234\n\nTechnical Arsenal\nPython, SQL'
    candidates, _ = resume_suggestions.heading_candidates(text, 'checksum')
    assert not any(c['heading'] == 'Avery Example' for c in candidates)
    assert any(c['heading'] == 'Technical Arsenal' for c in candidates)


async def test_owner_consent_and_heading_suggestions(client, make_pdf, monkeypatch):
    headers = await auth_headers(client)
    uploaded = (await upload_resume(client, headers, make_pdf('Candidate\n\nToolbox\nPython, SQL'))).json()['data']
    path = f"/api/v1/resumes/{uploaded['resume']['id']}/suggestions"
    calls = []
    async def evaluate(self, items):
        calls.extend(items)
        return {i['id']: {'choice': 'skills', 'confidence': 0.98, 'winner_probability': 0.99}
                for i in items if 'Toolbox' in i['text']}
    monkeypatch.setattr(jev.JevOperation, 'evaluate', evaluate)
    other = await auth_headers(client, 'other-jev@example.com')
    assert (await client.post(path, headers=other, json={'consent': True})).status_code == 404
    assert (await client.post(path, headers=headers, json={'consent': False})).status_code == 422
    assert calls == []
    response = await client.post(path, headers=headers, json={'consent': True})
    assert response.status_code == 200
    result = response.json()['data']
    assert result['profile_version'] == uploaded['profile']['version']
    assert result['resume_checksum'] == uploaded['resume']['checksum']
    assert any(s['heading'] == 'Toolbox' for s in result['suggestions'])
    assert 'Python' in result['suggested_fields']['skills']
    current = (await client.get('/api/v1/profiles/me', headers=headers)).json()['data']
    assert current['skills'] == uploaded['profile']['skills']


async def test_jev_supplemental_sections_copy_source_without_saving(client, make_pdf, monkeypatch):
    headers = await auth_headers(client)
    uploaded = (await upload_resume(client, headers, make_pdf(
        'Synthetic Candidate\nsynthetic@example.com\n\nMy Credentials\n- First Source Certificate\n\n'
        'Career Highlights\n- Won a source-stated contest.'))).json()['data']
    async def evaluate(self, items):
        return {i['id']: {'choice': 'certifications' if i['text'].startswith('My Credentials') else 'achievements',
                          'confidence': 0.98, 'winner_probability': 0.99}
                for i in items if i['text'].startswith(('My Credentials', 'Career Highlights'))}
    monkeypatch.setattr(jev.JevOperation, 'evaluate', evaluate)
    result = (await client.post(f"/api/v1/resumes/{uploaded['resume']['id']}/suggestions",
        headers=headers, json={'consent': True})).json()['data']
    assert result['suggested_fields']['certifications'] == ['First Source Certificate']
    assert result['suggested_fields']['achievements'] == ['Won a source-stated contest.']
    assert (await client.get('/api/v1/profiles/me', headers=headers)).json()['data'] == uploaded['profile']


async def test_disabled_assistance_is_visible_and_never_calls_provider(client, make_pdf, monkeypatch):
    headers = await auth_headers(client)
    uploaded = (await upload_resume(client, headers, make_pdf('Candidate\n\nToolbox\nPython'))).json()['data']
    async def forbidden(*args): pytest.fail('Unexpected provider request')
    monkeypatch.setattr(jev.JevOperation, 'request', forbidden)
    response = await client.post(f"/api/v1/resumes/{uploaded['resume']['id']}/suggestions", headers=headers, json={'consent': True})
    assert response.json()['data']['status'] == 'unavailable'
    assert response.json()['data']['suggestions'] == []


async def test_repeated_requests_share_work_limits(client, make_pdf, monkeypatch):
    from app.core.config import get_settings
    headers = await auth_headers(client)
    uploaded = (await upload_resume(client, headers, make_pdf('Candidate\nSkills\nPython'))).json()['data']
    monkeypatch.setattr(get_settings(), 'work_user_limit', 1)
    path = f"/api/v1/resumes/{uploaded['resume']['id']}/suggestions"
    assert (await client.post(path, headers=headers, json={'consent': True})).status_code == 200
    assert (await client.post(path, headers=headers, json={'consent': True})).status_code == 429


async def test_uncertain_heading_is_labeled_and_requires_editor_acceptance(client,make_pdf,monkeypatch):
    headers=await auth_headers(client)
    uploaded=(await upload_resume(client,headers,make_pdf('Avery Example\navery@example.com\n\nToolbox\nPython, SQL'))).json()['data']
    async def evaluate(self,items):
        return {i['id']:{'choice':'skills','confidence':0.79,'winner_probability':0.83} for i in items if i['text'].startswith('Toolbox')}
    monkeypatch.setattr(jev.JevOperation,'evaluate',evaluate)
    response=await client.post(f"/api/v1/resumes/{uploaded['resume']['id']}/suggestions",headers=headers,json={'consent':True})
    data=response.json()['data']
    assert data['suggestions'][0]['uncertain']
    assert data['suggested_fields']['skills']==['Python','SQL']
    current=(await client.get('/api/v1/profiles/me',headers=headers)).json()['data']
    assert current==uploaded['profile']
