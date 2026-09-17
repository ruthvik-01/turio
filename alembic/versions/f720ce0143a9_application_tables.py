"""Persist application preparation, review, tracking and idempotency.

Revision ID: f720ce0143a9
Revises: d68b174af012
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "f720ce0143a9"
down_revision = "d68b174af012"
branch_labels = None
depends_on = None
JSON = postgresql.JSONB().with_variant(sa.JSON(), "sqlite")


def upgrade():
    op.create_table("applications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("resume_id", sa.Uuid(), sa.ForeignKey("resumes.id", ondelete="SET NULL")),
        sa.Column("application_url", sa.String(2048), nullable=False),
        sa.Column("platform", sa.String(64)),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("outcome", sa.String(32)),
        sa.Column("notes", sa.Text()),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("profile_version", sa.Integer()),
        sa.Column("form_schema", JSON),
        sa.Column("review_snapshot", JSON),
        sa.Column("review_token", sa.String(64)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("submission_method", sa.String(16)),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    for key in ("user_id", "job_id"):
        op.create_index(f"ix_applications_{key}", "applications", [key])
    op.create_table("application_fields",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("application_id", sa.Uuid(), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_key", sa.String(128), nullable=False),
        sa.Column("label", sa.String(1024), nullable=False),
        sa.Column("input_type", sa.String(32), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("source_locator", sa.String(1024), nullable=False),
        sa.Column("normalized_intent", sa.String(64), nullable=False),
        sa.Column("options", JSON, nullable=False),
        sa.UniqueConstraint("application_id", "field_key"))
    op.create_index("ix_application_fields_application_id", "application_fields", ["application_id"])
    op.create_table("application_answers",
        sa.Column("field_id", sa.Uuid(), sa.ForeignKey("application_fields.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("value", JSON),
        sa.Column("value_source", sa.String(32), nullable=False),
        sa.Column("user_confirmed", sa.Boolean(), nullable=False))
    op.create_table("saved_answers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_key", sa.String(64), nullable=False),
        sa.Column("value", JSON, nullable=False),
        sa.UniqueConstraint("user_id", "question_key"))
    op.create_index("ix_saved_answers_user_id", "saved_answers", ["user_id"])
    op.create_table("application_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("application_id", sa.Uuid(), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("event_data", JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_application_events_application_id", "application_events", ["application_id"])
    op.create_table("idempotency_records",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("response", JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_idempotency_records_user_id", "idempotency_records", ["user_id"])


def downgrade():
    for table in ("idempotency_records", "application_events", "saved_answers", "application_answers", "application_fields", "applications"):
        op.drop_table(table)
