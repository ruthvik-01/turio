"""Rename legacy `jev_profile` answer provenance to `ai_profile`.

`application_answers.value_source` is a plain string column holding
`'profile'`, `'user'`, `'application_only'`, `'saved_answer'`, `'draft'` and
the legacy `'jev_profile'`. The legacy provider (TypeSafe) is removed, so the
stored value is renamed to match the neutral `ai_profile` source the code now
writes. No column, index or constraint changes.

`application_events.event_type` also carries `jev_*` names in historical rows.
Those rows are immutable audit records and are left untouched: the read path
only looks for the current `ai_*` names, so old events simply stop matching.

Revision ID: a231027001
Revises: a231026001
"""

from alembic import op

revision = "a231027001"
down_revision = "a231026001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE application_answers SET value_source = 'ai_profile' WHERE value_source = 'jev_profile'")


def downgrade() -> None:
    op.execute("UPDATE application_answers SET value_source = 'jev_profile' WHERE value_source = 'ai_profile'")
