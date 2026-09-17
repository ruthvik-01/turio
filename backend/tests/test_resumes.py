"""Phase 2 resume ingestion (PHASE_PLAN.md Phase 2, DATA_PIPELINE.md section 1)."""

import hashlib
from collections.abc import Callable

import pytest
from httpx import AsyncClient

from support import RESUME_TEXT, auth_headers, upload_resume

PDF = "application/pdf"


async def test_pdf_with_generic_browser_mime_is_validated_and_reused(client, make_pdf, storage):
    headers = await auth_headers(client)
    original = make_pdf(RESUME_TEXT)
    uploaded = await upload_resume(client, headers, original, content_type="application/octet-stream")
    assert uploaded.status_code == 201, uploaded.text
    assert uploaded.json()["data"]["resume"]["mime_type"] == PDF
    again = await upload_resume(client, headers, original)
    assert again.status_code == 200
    assert again.json()["data"]["resume"]["id"] == uploaded.json()["data"]["resume"]["id"]
    assert len(storage.put_calls) == 1
    invalid = await upload_resume(client, headers, b"not a PDF", content_type="application/octet-stream")
    assert invalid.status_code == 415


async def test_upload_extracts_the_profile(
    client: AsyncClient, make_pdf: Callable[[str], bytes]
) -> None:
    headers = await auth_headers(client)

    response = await upload_resume(client, headers, make_pdf(RESUME_TEXT))

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["error"] is None

    data = body["data"]
    assert data["reprocessed"] is True
    assert data["resume"]["mime_type"] == PDF
    assert data["resume"]["parser_version"]

    profile = data["profile"]
    assert profile["full_name"] == "Jane Doe"
    assert profile["location"] == "San Francisco, CA"
    assert {skill["name"] for skill in profile["skills"]} == {
        "Python",
        "FastAPI",
        "PostgreSQL",
        "Docker",
    }
    assert profile["experiences"][0]["title"] == "Senior Engineer"
    assert profile["experiences"][0]["company"] == "Acme Corp"
    assert profile["educations"][0]["institution"] == "Example University"


async def test_upload_requires_authentication(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/resumes", files={"file": ("resume.pdf", b"%PDF-1.4", PDF)}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.parametrize("filename", ["resume.txt", "resume.docx", "resume.pdf"])
async def test_non_pdf_uploads_are_rejected_with_a_stable_code(
    client: AsyncClient, filename: str
) -> None:
    headers = await auth_headers(client)

    response = await upload_resume(
        client, headers, b"not a pdf", filename=filename, content_type="text/plain"
    )

    assert response.status_code == 415
    body = response.json()
    assert body["data"] is None
    assert body["error"]["code"] == "INVALID_RESUME"


async def test_corrupt_pdf_is_rejected_rather_than_crashing(client: AsyncClient) -> None:
    headers = await auth_headers(client)

    response = await upload_resume(client, headers, b"%PDF-1.4\nthis is not really a pdf")

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "INVALID_RESUME"


async def test_empty_upload_is_rejected(client: AsyncClient) -> None:
    headers = await auth_headers(client)

    response = await upload_resume(client, headers, b"")

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "INVALID_RESUME"


async def test_oversized_upload_is_rejected_with_a_stable_code(
    client: AsyncClient, make_pdf: Callable[[str], bytes]
) -> None:
    headers = await auth_headers(client)
    oversized = make_pdf("x") + b"0" * (5 * 1024 * 1024)

    response = await upload_resume(client, headers, oversized)

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "INVALID_RESUME"


async def test_object_storage_outage_surfaces_as_503(
    client: AsyncClient, storage, make_pdf: Callable[[str], bytes]
) -> None:
    headers = await auth_headers(client)
    storage.fail = True

    response = await upload_resume(client, headers, make_pdf(RESUME_TEXT))

    assert response.status_code == 503
    body = response.json()
    assert body["data"] is None
    assert body["error"]["code"] == "OBJECT_STORAGE_UNAVAILABLE"


async def test_reuploading_identical_bytes_does_not_reprocess(
    client: AsyncClient, storage, make_pdf: Callable[[str], bytes]
) -> None:
    """PHASE_PLAN.md Phase 2 exit checklist item (b).

    Also asserts nothing was stored a second time, which is the part a status
    code alone would not catch.
    """
    headers = await auth_headers(client)
    pdf = make_pdf(RESUME_TEXT)

    first = await upload_resume(client, headers, pdf)
    assert first.status_code == 201
    assert len(storage.put_calls) == 1

    second = await upload_resume(client, headers, pdf)
    assert second.status_code == 200

    body = second.json()["data"]
    assert body["reprocessed"] is False
    assert body["resume"]["id"] == first.json()["data"]["resume"]["id"]
    # No second store, and no second parse.
    assert len(storage.put_calls) == 1

    stored_checksum = hashlib.sha256(pdf).hexdigest()
    assert body["resume"]["checksum"] == stored_checksum


async def test_different_bytes_create_a_second_resume(
    client: AsyncClient, make_pdf: Callable[[str], bytes]
) -> None:
    headers = await auth_headers(client)

    first = await upload_resume(client, headers, make_pdf(RESUME_TEXT))
    second = await upload_resume(client, headers, make_pdf(RESUME_TEXT + "\nExtra line"))

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["data"]["resume"]["id"] != second.json()["data"]["resume"]["id"]


async def test_empty_sections_produce_empty_values_never_invented_ones(
    client: AsyncClient, make_pdf: Callable[[str], bytes]
) -> None:
    """PHASE_PLAN.md Phase 2 exit checklist item (c)."""
    headers = await auth_headers(client)
    bare = "Jane Doe\njane.doe@example.com\n\nEXPERIENCE\n\nEDUCATION\n\nSKILLS\n"

    response = await upload_resume(client, headers, make_pdf(bare))

    assert response.status_code == 201, response.text
    profile = response.json()["data"]["profile"]
    assert profile["skills"] == []
    assert profile["experiences"] == []
    assert profile["educations"] == []
    assert profile["projects"] == []
    # A field the rules could not establish stays null.
    assert profile["location"] is None
    assert profile["phone"] is None


async def test_work_authorization_is_never_inferred_from_a_resume(
    client: AsyncClient, make_pdf: Callable[[str], bytes]
) -> None:
    """CLAUDE.md section 9: sensitive facts are collected, never derived."""
    headers = await auth_headers(client)
    text = (
        "Jane Doe\njane.doe@example.com\n\n"
        "Authorized to work in the United States. Will require visa sponsorship.\n\n"
        "SKILLS\nPython\n"
    )

    response = await upload_resume(client, headers, make_pdf(text))

    assert response.status_code == 201, response.text
    profile = response.json()["data"]["profile"]
    assert profile["work_authorization_status"] is None
    assert profile["sponsorship_required"] is None
