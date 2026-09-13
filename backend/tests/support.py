"""Helpers shared by the API test modules."""

from httpx import AsyncClient, Response

PASSWORD = "correct-horse-battery"

# A resume exercising every section the deterministic parser handles.
RESUME_TEXT = """Jane Doe
jane.doe@example.com | +1 555 010 1234 | San Francisco, CA
https://github.com/janedoe

SKILLS
Python, FastAPI, PostgreSQL, Docker

EXPERIENCE
Senior Engineer | Acme Corp | Jan 2020 - Present
Built things that mattered.

EDUCATION
B.Tech in Computer Science, Example University, 2018
"""


async def auth_headers(
    client: AsyncClient, email: str = "candidate@example.com"
) -> dict[str, str]:
    """Register a user and return an Authorization header for them."""
    response = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": PASSWORD}
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['data']['token']['access_token']}"}


async def upload_resume(
    client: AsyncClient,
    headers: dict[str, str],
    data: bytes,
    *,
    filename: str = "resume.pdf",
    content_type: str = "application/pdf",
) -> Response:
    return await client.post(
        "/api/v1/resumes",
        headers=headers,
        files={"file": (filename, data, content_type)},
    )
