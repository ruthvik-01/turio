"""Content-addressed embeddings and versioned recommendations.

Revision ID: d68b174af012
Revises: 72d80df90e65
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "d68b174af012"
down_revision = "72d80df90e65"
branch_labels = None
depends_on = None
JSON = postgresql.JSONB().with_variant(sa.JSON(), "sqlite")


def upgrade():
    op.create_table("embeddings",
        sa.Column("cache_key", sa.String(64), primary_key=True),
        sa.Column("vector", JSON, nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_embeddings_owner_user_id", "embeddings", ["owner_user_id"])
    op.create_table("job_matches",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("method", sa.String(16), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("model_version", sa.String(128), nullable=False),
        sa.Column("ranking_config_version", sa.String(64), nullable=False),
        sa.Column("inventory_hash", sa.String(64), nullable=False),
        sa.Column("profile_version", sa.Integer(), nullable=False),
        sa.Column("job_hash", sa.String(64), nullable=False),
        sa.Column("final_score", sa.Float(), nullable=False),
        sa.Column("explanation_payload", JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "job_id", "method"))
    op.create_index("ix_job_matches_user_id", "job_matches", ["user_id"])
    op.create_index("ix_job_matches_job_id", "job_matches", ["job_id"])


def downgrade():
    op.drop_table("job_matches")
    op.drop_table("embeddings")
