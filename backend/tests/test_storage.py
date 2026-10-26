import io

import pytest
from botocore.exceptions import ClientError

from app.core.errors import AppError
from app.core.storage import ObjectStorage


def object_store(**overrides):
    options = dict(
        endpoint="http://storage.invalid",
        access_key="test",
        secret_key="test",
        region="us-east-1",
        bucket="test",
    )
    options.update(overrides)
    return ObjectStorage(**options)


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


async def test_ensure_bucket_disabled_never_creates(monkeypatch):
    """Supabase Storage has no CreateBucket; the check must stay read-only."""
    store = object_store(ensure_bucket=False)
    calls = []

    def head(**kwargs):
        calls.append("head")
        raise ClientError({"Error": {"Code": "404"}}, "HeadBucket")

    def create(**kwargs):
        calls.append("create")

    monkeypatch.setattr(store._client, "head_bucket", head)
    monkeypatch.setattr(store._client, "create_bucket", create)

    with pytest.raises(ClientError):
        await store._ensure_bucket()
    assert calls == ["head"]
    assert store._bucket_checked is False


async def test_ensure_bucket_enabled_creates_when_missing(monkeypatch):
    store = object_store(ensure_bucket=True)
    calls = []

    def head(**kwargs):
        calls.append("head")
        raise ClientError({"Error": {"Code": "404"}}, "HeadBucket")

    def create(**kwargs):
        calls.append("create")

    monkeypatch.setattr(store._client, "head_bucket", head)
    monkeypatch.setattr(store._client, "create_bucket", create)

    await store._ensure_bucket()
    assert calls == ["head", "create"]
    assert store._bucket_checked is True


async def test_ensure_bucket_skips_when_present(monkeypatch):
    store = object_store(ensure_bucket=False)
    calls = []

    monkeypatch.setattr(store._client, "head_bucket", lambda **kwargs: calls.append("head"))
    monkeypatch.setattr(store._client, "create_bucket", lambda **kwargs: calls.append("create"))

    await store._ensure_bucket()
    assert calls == ["head"]


def test_client_uses_path_style_and_conditional_checksums():
    """Both matter for Supabase Storage: vhost addressing does not resolve, and
    botocore 1.43's default checksum headers are rejected by some providers."""
    store = object_store()
    assert store._client.meta.config.s3["addressing_style"] == "path"
    assert store._client.meta.config.request_checksum_calculation == "when_required"
    assert store._client.meta.config.signature_version == "s3v4"


async def test_put_failure_reports_storage_unavailable(monkeypatch):
    store = object_store(ensure_bucket=False)
    monkeypatch.setattr(store._client, "head_bucket", lambda **kwargs: None)

    def put(**kwargs):
        raise ClientError({"Error": {"Code": "AccessDenied"}}, "PutObject")

    monkeypatch.setattr(store._client, "put_object", put)
    with pytest.raises(AppError) as caught:
        await store.put("resumes/u/c.pdf", b"fixture", "application/pdf")
    assert caught.value.code == "OBJECT_STORAGE_UNAVAILABLE"


async def test_get_missing_object_reports_storage_unavailable(monkeypatch):
    store = object_store(ensure_bucket=False)

    def get(**kwargs):
        raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")

    monkeypatch.setattr(store._client, "get_object", get)
    with pytest.raises(AppError) as caught:
        await store.get("resumes/u/missing.pdf")
    assert caught.value.code == "OBJECT_STORAGE_UNAVAILABLE"


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
