"""Source-backed AI interpretation; no generated candidate values."""
import json
from datetime import date

import pytest
from pydantic import SecretStr
from app.adapters import assistance, openrouter
from app.services import resume_interpretation
from support import auth_headers, upload_resume

SOURCE = '''Synthetic Candidate
synthetic@example.com
EXPERIENCE
North Star Studio
Platform Wrangler
May 2020 - Present
Built reliable APIs.
PROJECTS
First Atlas
Developed a client.
Built Atlas
Implemented a service.
'''


def choices(items):
    labels = {'North Star Studio': 'company', 'Platform Wrangler': 'title',
        'May 2020 - Present': 'dates', 'Built reliable APIs.': 'description',
        'First Atlas': 'title', 'Developed a client.': 'description',
        'Built Atlas': 'title', 'Implemented a service.': 'description'}
    result = {}
    for item in items:
        if item['id'].startswith('fact-'):
            role = labels.get(json.loads(item['text'])['target'], 'other')
            result[item['id']] = {'choice': role, 'confidence': 0.98, 'winner_probability': 0.99}
        else:
            result[item['id']] = {'choice': 'none', 'confidence': 0.98, 'winner_probability': 0.99}
    return result


def test_fact_sources_keep_offsets_and_exclude_contact_legal_lines():
    source = SOURCE + 'Salary expectation: 1000\nI require visa sponsorship.\nemail: private@example.com\n'
    records = resume_interpretation.fact_candidates(source, {}, 'checksum')
    assert records
    for record in records:
        assert source[record['start']:record['end']] == record['heading']
        assert source[record['context_start']:record['context_end']] == record['excerpt']
        if record['item']:
            sent = record['item']['text']
            assert 'private@example.com' not in sent and 'visa sponsorship' not in sent and 'Salary expectation' not in sent
    assert any(record['item'] is None for record in records)


async def test_ai_roles_recover_non_lexicon_role_and_project_boundaries():
    op = assistance.AssistanceOperation(True)
    async def evaluate(items): return choices(items)
    op.evaluate = evaluate
    fields, evidence, unresolved = await resume_interpretation.interpret(op, SOURCE, {}, 'checksum')
    assert fields['experiences'] == [{'company': 'North Star Studio', 'title': 'Platform Wrangler',
        'start_date': date(2020, 5, 1), 'end_date': None, 'description': 'Built reliable APIs.'}]
    assert [p['name'] for p in fields['projects']] == ['First Atlas', 'Built Atlas']
    assert [p['description'] for p in fields['projects']] == ['Developed a client.', 'Implemented a service.']
    assert unresolved == 0
    assert any(record['section'] == 'experience:title' for record in evidence)


async def test_project_technologies_remain_source_backed_after_model_grouping():
    source = SOURCE.replace('Implemented a service.', 'Implemented a service using Python.') + 'SKILLS\nPython\n'
    op = assistance.AssistanceOperation(True)
    async def evaluate(items):
        result = choices(items)
        for item in items:
            target = json.loads(item['text'])['target']
            if target in {'Implemented a service using Python.', 'Python'}:
                result[item['id']]['choice'] = 'skills' if target == 'Python' else 'description'
        return result
    op.evaluate = evaluate
    fields, _, _ = await resume_interpretation.interpret(op, source, {}, 'checksum')
    assert fields['projects'][1]['technologies'] == ['Python']
    assert fields['skills'] == ['Python']


async def test_incomplete_section_cannot_replace_profile_with_partial_entities():
    op = assistance.AssistanceOperation(True)
    async def evaluate(items):
        decisions = choices(items)
        decisions.pop(next(item['id'] for item in items if json.loads(item['text'])['target'] == 'Built Atlas'))
        return decisions
    op.evaluate = evaluate
    fields, _, unresolved = await resume_interpretation.interpret(op, SOURCE, {}, 'checksum')
    assert 'projects' not in fields
    assert fields['experiences'][0]['title'] == 'Platform Wrangler'
    assert unresolved == 1


async def test_provider_cannot_supply_an_unoffered_role_or_invented_value():
    op = assistance.AssistanceOperation(True)
    async def evaluate(items):
        return {item['id']: {'choice': 'Invented Corporation', 'confidence': 0.99, 'winner_probability': 0.99} for item in items}
    op.evaluate = evaluate
    fields, evidence, unresolved = await resume_interpretation.interpret(op, SOURCE, {}, 'checksum')
    assert fields == {} and evidence == [] and unresolved > 0


async def test_profile_change_during_interpretation_discards_all_proposals(client, make_pdf, monkeypatch):
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), 'assistance_enabled', True)
    monkeypatch.setattr(openrouter, 'load_key', lambda: SecretStr('synthetic-test-only'))
    headers = await auth_headers(client)
    uploaded = (await upload_resume(client, headers, make_pdf(SOURCE))).json()['data']
    changed = False
    async def evaluate(self, items):
        nonlocal changed
        if any(item['id'].startswith('fact-') for item in items) and not changed:
            changed = True
            response = await client.patch('/api/v1/profiles/me', headers=headers, json={'full_name':'User Edited Candidate'})
            assert response.status_code == 200
        return choices(items)
    monkeypatch.setattr(assistance.AssistanceOperation, 'evaluate', evaluate)
    response = await client.post(f"/api/v1/resumes/{uploaded['resume']['id']}/suggestions", headers=headers, json={'consent':True})
    data = response.json()['data']
    assert data['status'] == 'stale' and data['suggested_fields'] == {} and data['suggestions'] == []
    assert (await client.get('/api/v1/profiles/me', headers=headers)).json()['data']['full_name'] == 'User Edited Candidate'


async def test_existing_consent_api_returns_source_facts_without_profile_mutation(client, make_pdf, monkeypatch):
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), 'assistance_enabled', True)
    monkeypatch.setattr(openrouter, 'load_key', lambda: SecretStr('synthetic-test-only'))
    async def evaluate(self, items): return choices(items)
    monkeypatch.setattr(assistance.AssistanceOperation, 'evaluate', evaluate)
    headers = await auth_headers(client)
    original = (await upload_resume(client, headers, make_pdf(SOURCE))).json()['data']
    path = f"/api/v1/resumes/{original['resume']['id']}/suggestions"
    assert (await client.post(path, headers=headers, json={'consent':False})).status_code == 422
    response = await client.post(path, headers=headers, json={'consent':True})
    assert response.status_code == 200
    data = response.json()['data']
    assert data['suggested_fields']['experiences'][0]['title'] == 'Platform Wrangler'
    assert len(data['suggested_fields']['projects']) == 2
    assert data['profile_version'] == original['profile']['version']
    assert data['resume_checksum'] == original['resume']['checksum']
    assert (await client.get('/api/v1/profiles/me', headers=headers)).json()['data'] == original['profile']
