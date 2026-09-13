"""Database column types shared by the models."""

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator

# JSONB is the deployment target. SQLite has no JSONB, so it gets plain JSON -
# otherwise the suite could not run without a container runtime.
JsonB = JSONB().with_variant(JSON(), "sqlite")


class UTCDateTime(TypeDecorator):
    """A timestamp that is always timezone-aware UTC.

    PostgreSQL stores this natively as `timestamptz`. SQLite has no timezone
    support and hands back naive values, so results are re-tagged as UTC on
    read. Without that, an expiry comparison would raise on SQLite and pass on
    PostgreSQL - the worst way for the two backends to disagree.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: object) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("UTCDateTime requires a timezone-aware datetime")
        return value.astimezone(timezone.utc)

    def process_result_value(self, value: datetime | None, dialect: object) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
