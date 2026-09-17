"""Shared rate counters and bounded browser-operation ownership.

Revision ID: e86f201cb945
Revises: b491ef087a52
"""
import sqlalchemy as sa
from alembic import op

revision = "e86f201cb945"
down_revision = "b491ef087a52"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("rate_limit_buckets",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("count", sa.BigInteger(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_rate_limit_buckets_expires_at", "rate_limit_buckets", ["expires_at"])
    op.add_column("applications", sa.Column("operation_token", sa.Uuid()))
    op.add_column("applications", sa.Column("operation_kind", sa.String(16)))
    op.add_column("applications", sa.Column("operation_expires_at", sa.DateTime(timezone=True)))
    op.add_column("applications", sa.Column("operation_request_key", sa.String(64)))
    op.create_index("ix_applications_operation_expires_at", "applications", ["operation_expires_at"])


def downgrade():
    op.drop_index("ix_applications_operation_expires_at", table_name="applications")
    for column in ("operation_request_key", "operation_expires_at", "operation_kind", "operation_token"):
        op.drop_column("applications", column)
    op.drop_table("rate_limit_buckets")
