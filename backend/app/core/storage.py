"""S3-compatible object storage for resume binaries.

DATABASE.md section 1 keeps the file itself out of PostgreSQL; only the storage
key is stored. boto3 is synchronous, so every call is handed to a worker thread
rather than blocking the event loop.
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
    ) -> None:
        self._bucket = bucket
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
                # MinIO serves path-style addressing by default; virtual-host
                # style would try to resolve the bucket as a subdomain.
                s3={"addressing_style": "path"},
            ),
        )

    @property
    def bucket(self) -> str:
        return self._bucket

    async def _ensure_bucket(self) -> None:
        """Create the bucket on first use.

        Done lazily rather than at startup so that object storage being down
        cannot stop the API from booting.
        """
        if self._bucket_checked:
            return

        def _head_then_create() -> None:
            try:
                self._client.head_bucket(Bucket=self._bucket)
            except ClientError:
                self._client.create_bucket(Bucket=self._bucket)

        await asyncio.to_thread(_head_then_create)
        self._bucket_checked = True

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        await self._ensure_bucket()

        def _put() -> None:
            self._client.put_object(
                Bucket=self._bucket, Key=key, Body=data, ContentType=content_type
            )

        try:
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
