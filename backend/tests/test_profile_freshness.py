from support import auth_headers


async def test_expected_version_rejects_stale_whole_update(client):
    headers = await auth_headers(client)
    first = (await client.get('/api/v1/profiles/me', headers=headers)).json()['data']
    accepted = await client.patch('/api/v1/profiles/me', headers=headers,
        json={'expected_profile_version': first['version'], 'phone': '123', 'skills': ['Python']})
    assert accepted.status_code == 200
    stale = await client.patch('/api/v1/profiles/me', headers=headers,
        json={'expected_profile_version': first['version'], 'phone': '999', 'skills': ['Go']})
    assert stale.status_code == 409
    current = (await client.get('/api/v1/profiles/me', headers=headers)).json()['data']
    assert current['phone'] == '123'
    assert [s['name'] for s in current['skills']] == ['Python']
    assert current['version'] == first['version'] + 1


async def test_old_clients_can_omit_version(client):
    headers = await auth_headers(client)
    response = await client.patch('/api/v1/profiles/me', headers=headers, json={'phone': '123'})
    assert response.status_code == 200
