"""Phase 2 profile reads and user-confirmed edits (API_SPEC.md section 3)."""

from collections.abc import Callable

from httpx import AsyncClient

from support import RESUME_TEXT, auth_headers, upload_resume


async def test_profile_is_empty_before_any_resume_is_uploaded(client: AsyncClient) -> None:
    headers = await auth_headers(client)

    response = await client.get("/api/v1/profiles/me", headers=headers)

    assert response.status_code == 200
    profile = response.json()["data"]
    assert profile["full_name"] is None
    assert profile["skills"] == []
    assert profile["version"] == 1


async def test_profile_requires_authentication(client: AsyncClient) -> None:
    read = await client.get("/api/v1/profiles/me")
    write = await client.patch("/api/v1/profiles/me", json={"full_name": "x"})

    for response in (read, write):
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_user_edits_are_what_the_profile_returns(
    client: AsyncClient, make_pdf: Callable[[str], bytes]
) -> None:
    """PHASE_PLAN.md Phase 2 exit checklist item (d).

    The extraction is deliberately wrong here, so the assertion fails if the
    stored parse is ever returned in place of the user's correction.
    """
    headers = await auth_headers(client)
    await upload_resume(client, headers, make_pdf(RESUME_TEXT))

    corrected = {
        "full_name": "Jane A. Doe",
        "location": "Oakland, CA",
        "preferred_roles": ["Backend Engineer"],
        "skills": ["Python", "Kubernetes"],
        "experiences": [
            {
                "company": "Acme Corporation",
                "title": "Staff Engineer",
                "start_date": "2020-01-01",
                "end_date": None,
                "description": "Led the platform team.",
            }
        ],
    }

    patched = await client.patch("/api/v1/profiles/me", headers=headers, json=corrected)
    assert patched.status_code == 200, patched.text

    fetched = await client.get("/api/v1/profiles/me", headers=headers)
    profile = fetched.json()["data"]

    assert profile["full_name"] == "Jane A. Doe"
    assert profile["location"] == "Oakland, CA"
    assert profile["preferred_roles"] == ["Backend Engineer"]
    assert [skill["name"] for skill in profile["skills"]] == ["Python", "Kubernetes"]
    assert profile["experiences"][0]["company"] == "Acme Corporation"
    assert profile["experiences"][0]["title"] == "Staff Engineer"
    # The parsed value is gone, not merged alongside the correction.
    assert all(item["company"] != "Acme Corp" for item in profile["experiences"])


async def test_partial_update_leaves_other_fields_alone(
    client: AsyncClient, make_pdf: Callable[[str], bytes]
) -> None:
    headers = await auth_headers(client)
    await upload_resume(client, headers, make_pdf(RESUME_TEXT))

    await client.patch("/api/v1/profiles/me", headers=headers, json={"full_name": "J. Doe"})

    profile = (await client.get("/api/v1/profiles/me", headers=headers)).json()["data"]
    assert profile["full_name"] == "J. Doe"
    # Untouched by that request, so still whatever extraction produced.
    assert profile["location"] == "San Francisco, CA"
    assert profile["skills"]


async def test_sending_only_skills_does_not_wipe_experience(
    client: AsyncClient, make_pdf: Callable[[str], bytes]
) -> None:
    headers = await auth_headers(client)
    await upload_resume(client, headers, make_pdf(RESUME_TEXT))

    await client.patch("/api/v1/profiles/me", headers=headers, json={"skills": ["Go"]})

    profile = (await client.get("/api/v1/profiles/me", headers=headers)).json()["data"]
    assert [skill["name"] for skill in profile["skills"]] == ["Go"]
    assert profile["experiences"], "an unrelated entity set was cleared"


async def test_explicit_null_clears_a_field(client: AsyncClient) -> None:
    headers = await auth_headers(client)
    await client.patch("/api/v1/profiles/me", headers=headers, json={"full_name": "Set Me"})

    await client.patch("/api/v1/profiles/me", headers=headers, json={"full_name": None})

    profile = (await client.get("/api/v1/profiles/me", headers=headers)).json()["data"]
    assert profile["full_name"] is None


async def test_every_edit_advances_the_profile_version(client: AsyncClient) -> None:
    """ADR-019: cached matching keys off profile.version, so it must move."""
    headers = await auth_headers(client)

    first = (await client.get("/api/v1/profiles/me", headers=headers)).json()["data"]["version"]
    await client.patch("/api/v1/profiles/me", headers=headers, json={"full_name": "One"})
    second = (await client.get("/api/v1/profiles/me", headers=headers)).json()["data"]["version"]
    await client.patch("/api/v1/profiles/me", headers=headers, json={"full_name": "Two"})
    third = (await client.get("/api/v1/profiles/me", headers=headers)).json()["data"]["version"]

    assert first < second < third


async def test_users_cannot_see_each_others_profiles(
    client: AsyncClient, make_pdf: Callable[[str], bytes]
) -> None:
    alice = await auth_headers(client, email="alice@example.com")
    bob = await auth_headers(client, email="bob@example.com")

    await upload_resume(client, alice, make_pdf(RESUME_TEXT))
    await client.patch("/api/v1/profiles/me", headers=alice, json={"full_name": "Alice"})

    bob_profile = (await client.get("/api/v1/profiles/me", headers=bob)).json()["data"]

    assert bob_profile["full_name"] != "Alice"
    assert bob_profile["full_name"] is None
    assert bob_profile["skills"] == []
