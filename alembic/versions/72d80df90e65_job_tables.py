"""job tables

Revision ID: 72d80df90e65
Revises: c3a82f12a934
Create Date: 2026-09-13 23:56:21.781757

Generated with `alembic revision --autogenerate`, then adjusted the same way as
the previous two revisions: `app.models.types.UTCDateTime` is written out as
`sa.DateTime(timezone=True)` and the unqualified `Text()` it emits becomes
`sa.Text()`. A migration must not import application code, or it stops applying
whenever that code changes.

`uq_jobs_source_external_id` is the constraint that makes re-ingestion
idempotent — a posting seen twice is one row (DATABASE.md section 6).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "72d80df90e65"
down_revision: str | None = "c3a82f12a934"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_JsonB = postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "job_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("base_url", sa.String(length=512), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=512), nullable=True),
        sa.Column("job_url", sa.String(length=1024), nullable=False),
        sa.Column("application_url", sa.String(length=1024), nullable=True),
        sa.Column("ats", sa.String(length=64), nullable=True),
        sa.Column("required_skills", _JsonB, nullable=True),
        sa.Column("required_education", _JsonB, nullable=True),
        sa.Column("experience_requirement", _JsonB, nullable=True),
        sa.Column("raw_payload", _JsonB, nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["job_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "external_id", name="uq_jobs_source_external_id"),
    )

    op.create_index(op.f("ix_jobs_ats"), "jobs", ["ats"], unique=False)
    op.create_index(op.f("ix_jobs_company"), "jobs", ["company"], unique=False)
    op.create_index(op.f("ix_jobs_content_hash"), "jobs", ["content_hash"], unique=False)
    op.create_index(op.f("ix_jobs_external_id"), "jobs", ["external_id"], unique=False)
    op.create_index(op.f("ix_jobs_location"), "jobs", ["location"], unique=False)
    op.create_index(op.f("ix_jobs_source_id"), "jobs", ["source_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_jobs_source_id"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_location"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_external_id"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_content_hash"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_company"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_ats"), table_name="jobs")
    op.drop_table("jobs")
    op.drop_table("job_sources")
