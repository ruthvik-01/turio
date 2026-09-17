"""Durable database jobs and fenced worker leases.

Revision ID: b491ef087a52
Revises: f720ce0143a9
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "b491ef087a52"
down_revision = "f720ce0143a9"
branch_labels = None
depends_on = None
JSON = postgresql.JSONB().with_variant(sa.JSON(), "sqlite")


def upgrade():
    op.create_table("agent_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_type", sa.String(32), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("resource_key", sa.String(128), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("payload", JSON, nullable=False),
        sa.Column("result", JSON),
        sa.Column("worker_id", sa.String(128)),
        sa.Column("lease_token", sa.Uuid()),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True)),
        sa.Column("error_code", sa.String(64)),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("run_type IN ('jobs_refresh','matches_refresh')", name="ck_agent_runs_type"),
        sa.CheckConstraint("state IN ('queued','running','succeeded','failed','interrupted','cancelled')", name="ck_agent_runs_state"))
    for column in ("user_id", "state", "lease_expires_at"):
        op.create_index(f"ix_agent_runs_{column}", "agent_runs", [column])
    op.create_index("uq_agent_runs_active_resource", "agent_runs", ["resource_key"], unique=True,
        postgresql_where=sa.text("state IN ('queued','running')"),
        sqlite_where=sa.text("state IN ('queued','running')"))


def downgrade():
    op.drop_table("agent_runs")
