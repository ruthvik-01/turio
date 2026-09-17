import io

import pytest
from botocore.exceptions import ClientError

from app.core.errors import AppError
from app.core.storage import ObjectStorage


def object_store():
    return ObjectStorage(endpoint="http://storage.invalid", access_key="test", secret_key="test", region="us-east-1", bucket="test")


async def test_bucket_initialization_outage_uses_storage_error(monkeypatch):
    store = object_store()

    async def unavailable():
        raise ClientError({"Error": {"Code": "AccessDenied"}}, "HeadBucket")

    monkeypatch.setattr(store, "_ensure_bucket", unavailable)
    with pytest.raises(AppError) as caught:
        await store.put("resume.pdf", b"fixture", "application/pdf")
    assert caught.value.code == "OBJECT_STORAGE_UNAVAILABLE"


async def test_original_resume_read_closes_stream(monkeypatch):
    store = object_store()
    stream = io.BytesIO(b"original-fixture-bytes")
    monkeypatch.setattr(store._client, "get_object", lambda **kwargs: {"Body": stream})
    assert await store.get("owner/checksum.pdf") == b"original-fixture-bytes"
    assert stream.closed


async def test_browser_loader_checks_stored_resume_checksum(client, session, storage, make_pdf):
    from uuid import UUID, uuid4
    from app.api.v1.applications import get_adapter
    from support import RESUME_TEXT, auth_headers, upload_resume

    headers = await auth_headers(client, "resume-integrity@example.com")
    user_id = UUID((await client.get("/api/v1/auth/me", headers=headers)).json()["data"]["id"])
    original = make_pdf(RESUME_TEXT)
    uploaded = await upload_resume(client, headers, original)
    assert uploaded.status_code == 201
    resume_id = uploaded.json()["data"]["resume"]["id"]
    adapter = get_adapter(uuid4(), user_id, session, storage)
    assert (await adapter.load_resume(resume_id))[1] == original
    storage.objects[storage.put_calls[0]] = b"corrupted object"
    with pytest.raises(AppError) as caught:
        await adapter.load_resume(resume_id)
    assert caught.value.code == "OBJECT_STORAGE_UNAVAILABLE"
