"""Actual PostgreSQL locks, independent connections and concurrent writes."""
import asyncio
from uuid import UUID

import pytest
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.adapters.assistance import assistance
from app.adapters import openrouter
from app.core.config import get_settings
from app.core.errors import AppError
from app.repositories import profiles
from app.schemas.profile import ProfileUpdateRequest
from app.services.profile import update_profile
from app.services.resume_pipeline import ingest_resume
from support import auth_headers


async def owner(client):
    headers = await auth_headers(client)
    user = (await client.get('/api/v1/auth/me', headers=headers)).json()['data']
    profile = (await client.get('/api/v1/profiles/me', headers=headers)).json()['data']
    return UUID(user['id']), profile['version']


def postgres_only(engine):
    if engine.dialect.name != 'postgresql': pytest.skip('Requires isolated PostgreSQL test database')


async def test_concurrent_expected_saves_have_one_winner(database_engine, client):
    postgres_only(database_engine)
    user_id, version = await owner(client)
    factory = async_sessionmaker(database_engine, expire_on_commit=False)
    async def save(phone):
        async with factory() as session:
            try:
                return (await update_profile(session, user_id=user_id,
                    payload=ProfileUpdateRequest(expected_profile_version=version, phone=phone, skills=[phone]))).version
            except AppError as exc:
                return exc.http_status
    results = await asyncio.gather(save('first'), save('second'))
    assert sorted(results) == [version + 1, 409]


async def test_profile_lock_refreshes_preloaded_copy(database_engine, client):
    postgres_only(database_engine)
    user_id, version = await owner(client)
    factory = async_sessionmaker(database_engine, expire_on_commit=False)
    async with factory() as old, factory() as fresh:
        loaded = await profiles.get_or_create(old, user_id)
        await update_profile(fresh, user_id=user_id, payload=ProfileUpdateRequest(phone='new'))
        locked = await profiles.get_or_create(old, user_id, lock=True)
        assert loaded is locked and locked.version == version + 1 and locked.phone == 'new'


async def test_resume_write_serializes_stale_correction(database_engine, client, storage, make_pdf, monkeypatch):
    postgres_only(database_engine)
    user_id, version = await owner(client)
    factory = async_sessionmaker(database_engine, expire_on_commit=False)
    entered, release = asyncio.Event(), asyncio.Event()
    original = storage.put
    async def blocked_put(*args):
        entered.set()
        await release.wait()
        await original(*args)
    monkeypatch.setattr(storage, 'put', blocked_put)
    async def upload():
        async with factory() as session:
            return await ingest_resume(session, storage, user_id=user_id, filename='fixture.pdf',
                mime_type='application/pdf', data=make_pdf('Candidate\nSkills\nPython'))
    async def correction():
        async with factory() as session:
            return await update_profile(session, user_id=user_id,
                payload=ProfileUpdateRequest(expected_profile_version=version, phone='stale', skills=['Go']))
    task = asyncio.create_task(upload())
    await asyncio.wait_for(entered.wait(), 3)
    pending = asyncio.create_task(correction())
    try:
        with pytest.raises(TimeoutError): await asyncio.wait_for(asyncio.shield(pending), 0.1)
    finally:
        release.set()
    await task
    with pytest.raises(AppError) as error: await pending
    assert error.value.http_status == 409


async def test_advisory_limit_spans_independent_engines_and_releases(database_engine, client, monkeypatch):
    postgres_only(database_engine)
    monkeypatch.setattr(get_settings(), 'assistance_enabled', True)
    monkeypatch.setattr(openrouter, 'load_key', lambda: SecretStr('mock-only'))
    user_id, _ = await owner(client)
    other_engine = create_async_engine(database_engine.url)
    first = async_sessionmaker(database_engine)
    second = async_sessionmaker(other_engine)
    try:
        async with first() as one, second() as two:
            async with assistance(one, user_id):
                with pytest.raises(AppError) as error:
                    async with assistance(two, user_id): pytest.fail('Concurrent assistance admitted')
                assert error.value.http_status == 429
            async with assistance(two, user_id): pass
        entered = asyncio.Event()
        async def cancelled_operation():
            async with first() as session:
                async with assistance(session, user_id):
                    entered.set()
                    await asyncio.Event().wait()
        task = asyncio.create_task(cancelled_operation())
        await asyncio.wait_for(entered.wait(), 3)
        task.cancel()
        with pytest.raises(asyncio.CancelledError): await task
        async with second() as session:
            async with assistance(session, user_id): pass
    finally:
        await other_engine.dispose()
