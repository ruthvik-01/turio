"""Promote job availability to a stored column.

`raw_payload` holds the verbatim source record and averages 4 KB per row, so
PostgreSQL keeps it out of line (TOAST). Every `eligible()` filter reads
`raw_payload['_turio_availability']['status']`, which forces a detoast of all
25k rows: 12.5s for a `count(*)`, 23s for the inventory fingerprint. That is
longer than the frontend proxy's 15s GET timeout, so `/api/jobs` and
`/api/matches` returned 503.

A stored generated column keeps the same expression but computes it once on
write, where the row is already being written. The same `count(*)` drops to
17ms. Nothing else changes: the expression is identical, so no backfill logic
and no read-path edit is needed.

`application_deadline >= now()` cannot join the expression because `now()` is
VOLATILE, so that half of `eligible()` still runs as a filter. It is cheap —
the deadline is an ordinary indexed column.

Revision ID: a231026001
Revises: a231025001
"""

from alembic import op

revision = "a231026001"
down_revision = "a231025001"
branch_labels = None
depends_on = None

_EXPRESSION = "coalesce(raw_payload->'_turio_availability'->>'status', '')"


def upgrade() -> None:
    # Adding a stored generated column rewrites the table, so this is not
    # instant: ~77s for 25k rows. It is idempotent, which matters because the
    # revision may be re-run against a database where it already landed.
    op.execute(
        f"""
        ALTER TABLE jobs
        ADD COLUMN IF NOT EXISTS availability_status text
        GENERATED ALWAYS AS ({_EXPRESSION}) STORED
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE jobs DROP COLUMN IF EXISTS availability_status")
