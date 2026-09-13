"""Time helpers.

Every timestamp in Turio is timezone-aware UTC. Naive datetimes are rejected
at the database boundary (see `app.models.types.UTCDateTime`) rather than
silently compared against aware ones.
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
