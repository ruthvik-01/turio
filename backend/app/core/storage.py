"""S3-compatible object storage for resume binaries.

DATABASE.md section 1 keeps the file itself out of PostgreSQL; only the storage
key is stored. boto3 is synchronous, so every call is handed to a worker thread
rather than blocking the event loop.

The client speaks plain S3, so the same code serves MinIO in development and
Supabase Storage in deployment. Two provider differences are handled explicitly:

* Supabase Storage does not implement CreateBucket. Its buckets are provisioned
  through the dashboard or SQL, so `ensure_bucket` is disabled there and the
  startup check becomes a read-only HeadBucket.
* botocore 1.43 adds `x-amz-checksum-*` headers to PutObject by default. Several
  S3-compatible providers reject them, so checksums are only calculated when the
  operation actually requires one.
"""

import asyncio
import logging

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.errors import AppError

logger = logging.getLogger(__name__)

_CONNECT_TIMEOUT_SECONDS = 5
_READ_TIMEOUT_SECONDS = 30


class ObjectStorage:
    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        region: str,
        bucket: str,
        ensure_bucket: bool = True,
    ) -> None:
        self._bucket = bucket
        self._ensure_bucket_enabled = ensure_bucket
        self._bucket_checked = False
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(
                connect_timeout=_CONNECT_TIMEOUT_SECONDS,
                read_timeout=_READ_TIMEOUT_SECONDS,
                signature_version="s3v4",
                request_checksum_calculation="when_required",
                # MinIO and Supabase Storage both serve path-style addressing;
                # virtual-host style would try to resolve the bucket as a
                # subdomain of the storage host.
                s3={"addressing_style": "path"},
            ),
        )

    @property
    def bucket(self) -> str:
        return self._bucket

    async def _ensure_bucket(self) -> None:
        """Verify the bucket exists, creating it only when allowed.

        Done lazily rather than at startup so that object storage being down
        cannot stop the API from booting.
        """
        if self._bucket_checked:
            return

        def _head_then_maybe_create() -> None:
            try:
                self._client.head_bucket(Bucket=self._bucket)
            except ClientError:
                if not self._ensure_bucket_enabled:
                    # The bucket is provisioned out of band (Supabase Storage).
                    # Let the caller's operation surface the real error rather
                    # than attempting an unsupported CreateBucket.
                    raise
                self._client.create_bucket(Bucket=self._bucket)

        await asyncio.to_thread(_head_then_maybe_create)
        self._bucket_checked = True

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        def _put() -> None:
            self._client.put_object(
                Bucket=self._bucket, Key=key, Body=data, ContentType=content_type
            )

        try:
            await self._ensure_bucket()
            await asyncio.to_thread(_put)
        except (BotoCoreError, ClientError) as exc:
            logger.error(
                "object_storage_put_failed",
                extra={"extra_fields": {"key": key, "reason": type(exc).__name__}},
            )
            raise AppError(
                "OBJECT_STORAGE_UNAVAILABLE",
                "The uploaded file could not be stored.",
                503,
            ) from exc

    async def get(self, key: str) -> bytes:
        def _get() -> bytes:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
            try:
                return response["Body"].read()
            finally:
                response["Body"].close()

        try:
            return await asyncio.to_thread(_get)
        except (BotoCoreError, ClientError) as exc:
            raise AppError("OBJECT_STORAGE_UNAVAILABLE", "The stored resume could not be read.", 503) from exc
