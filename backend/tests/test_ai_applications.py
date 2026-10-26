import copy

from app.adapters import assistance
from test_applications import flow, FORM


async def prepare_ai(client, flow, monkeypatch):
    headers, app, adapter = flow
    form = copy.deepcopy(FORM)
    form['fields'].append({'field_key': 'phone', 'label': 'Best number to reach you',
        'input_type': 'text', 'required': True, 'source_locator': '#phone', 'options': []})
    async def inspect(url): return form
    adapter.inspect = inspect
    await client.patch('/api/v1/profiles/me', headers=headers, json={'phone': '123'})
    async def evaluate(self, items):
        assert not any('authorized' in item['text'] for item in items)
        return {item['id']: {'choice': 'phone', 'confidence': 0.99, 'winner_probability': 0.999}
            for item in items}
    monkeypatch.setattr(assistance.AssistanceOperation, 'evaluate', evaluate)
    prefix = f"/api/v1/applications/{app['id']}"
    response = await client.post(prefix + '/start', headers=headers, json={'ai_assist': True})
    assert response.status_code == 200, response.text
    data = response.json()['data']
    field = next(f for f in data['fields'] if f['field_key'] == 'phone')
    return headers, prefix, field, data


async def test_ai_confirmation_is_explicit_and_source_survives(client, flow, monkeypatch):
    headers, prefix, field, data = await prepare_ai(client, flow, monkeypatch)
    assert field['value'] == '123'
    assert field['value_source'] == 'ai_profile'
    assert field['user_confirmed'] is False
    async def save(key, value, **flags):
        response = await client.post(prefix + '/answers', headers={**headers, 'Idempotency-Key': key},
            json={'answers': [{'field_id': field['id'], 'value': value, **flags}]})
        assert response.status_code == 200, response.text
        return next(f for f in response.json()['data']['fields'] if f['id'] == field['id'])
    assert not (await save('edit', '456'))['user_confirmed']
    confirmed = await save('confirm', '456', ai_confirmed=True)
    assert confirmed['user_confirmed'] and confirmed['value_source'] == 'ai_profile'
    assert not (await save('reedit', '789'))['user_confirmed']
    assert any(e['event_type'] == 'ai_fields_mapped' for e in data['events'])


async def test_profile_change_rejects_confirmation_and_recomputes(client, flow, monkeypatch):
    headers, prefix, field, _ = await prepare_ai(client, flow, monkeypatch)
    await client.patch('/api/v1/profiles/me', headers=headers, json={'phone': '999'})
    response = await client.post(prefix + '/answers', headers={**headers, 'Idempotency-Key': 'stale'},
        json={'answers': [{'field_id': field['id'], 'value': '123', 'ai_confirmed': True}]})
    assert response.status_code == 409
    response = await client.post(prefix + '/start', headers=headers, json={'ai_assist': True})
    updated = next(f for f in response.json()['data']['fields'] if f['field_key'] == 'phone')
    assert updated['value'] == '999' and not updated['user_confirmed']


async def test_bodyless_prepare_never_uses_assistance(client, flow, monkeypatch):
    headers, app, _ = flow
    async def forbidden(*args): raise AssertionError('Unexpected assistance call')
    monkeypatch.setattr(assistance.AssistanceOperation, 'evaluate', forbidden)
    assert (await client.post(f"/api/v1/applications/{app['id']}/start", headers=headers)).status_code == 200


async def test_form_change_invalidates_ai_provenance(client, session, flow, monkeypatch):
    from sqlalchemy import select
    from app.models.application import ApplicationField
    headers, prefix, field, _ = await prepare_ai(client, flow, monkeypatch)
    stored = await session.scalar(select(ApplicationField).where(ApplicationField.field_key == 'phone'))
    stored.label = 'Different question'
    await session.commit()
    response = await client.post(prefix + '/answers', headers={**headers, 'Idempotency-Key': 'form-stale'},
        json={'answers': [{'field_id': field['id'], 'value': '123', 'ai_confirmed': True}]})
    assert response.status_code == 409


async def test_ai_answer_does_not_enter_saved_question_reuse(client, session, flow, monkeypatch):
    from sqlalchemy import select, func
    from app.models.application import SavedAnswer
    headers, prefix, field, _ = await prepare_ai(client, flow, monkeypatch)
    response = await client.post(prefix + '/answers', headers={**headers, 'Idempotency-Key': 'no-reuse'},
        json={'answers': [{'field_id': field['id'], 'value': '123', 'ai_confirmed': True, 'save_for_reuse': True}]})
    assert response.status_code == 200
    assert await session.scalar(select(func.count()).select_from(SavedAnswer)) == 0


async def test_failed_validation_preserves_existing_fields_and_answers(client, flow, monkeypatch):
    from app.core.errors import AppError
    from app.services import form_mapping
    from test_applications import prepared
    headers, app, adapter = flow
    prefix = await prepared(client, headers, app)
    before = (await client.get(prefix, headers=headers)).json()['data']['fields']
    original = form_mapping.validate_answer
    def invalid(field, value, resume_id):
        if field.field_key == 'name': raise AppError('MISSING_REQUIRED_FIELD', 'Fixture validation failure', 422)
        return original(field, value, resume_id)
    monkeypatch.setattr(form_mapping, 'validate_answer', invalid)
    response = await client.post(prefix + '/start', headers=headers)
    assert response.status_code == 422
    after = (await client.get(prefix, headers=headers)).json()['data']['fields']
    assert [(f['id'], f['value']) for f in after] == [(f['id'], f['value']) for f in before]


async def test_email_control_rejects_incompatible_ai_intent(client, flow, monkeypatch):
    headers, app, adapter = flow
    form = copy.deepcopy(FORM)
    form['fields'].insert(0, {'field_key': 'alternate', 'label': 'Best way to contact you', 'input_type': 'email',
        'required': True, 'source_locator': '#alternate', 'options': []})
    async def inspect(url): return form
    adapter.inspect = inspect
    async def evaluate(self, items):
        return {item['id']: {'choice': 'phone', 'confidence': 0.99, 'winner_probability': 0.999} for item in items}
    monkeypatch.setattr(assistance.AssistanceOperation, 'evaluate', evaluate)
    await client.patch('/api/v1/profiles/me', headers=headers, json={'phone': '123'})
    response = await client.post(f"/api/v1/applications/{app['id']}/start", headers=headers, json={'ai_assist': True})
    assert response.status_code == 200
    field = next(f for f in response.json()['data']['fields'] if f['field_key'] == 'alternate')
    assert field['value'] is None and field['value_source'] == 'missing'


async def test_uncertain_mapping_is_review_only_and_labeled(client, flow, monkeypatch):
    headers, prefix, _, _ = await prepare_ai(client, flow, monkeypatch)
    async def evaluate(self, items):
        return {item['id']:{'choice':'phone','confidence':0.79,'winner_probability':0.89} for item in items}
    monkeypatch.setattr(assistance.AssistanceOperation,'evaluate',evaluate)
    response=await client.post(prefix+'/start',headers=headers,json={'ai_assist':True})
    field=next(f for f in response.json()['data']['fields'] if f['field_key']=='phone')
    assert field['value']=='123' and not field['user_confirmed']
    assert field['ai_uncertain'] and field['ai_confidence']==0.79
