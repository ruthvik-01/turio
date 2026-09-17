"""Human research annotations with source/version provenance."""
import sqlalchemy as sa
from alembic import op

revision = "f192dea57304"
down_revision = "e86f201cb945"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("evaluation_annotations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resume_id", sa.Uuid(), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relevance_label", sa.Integer(), nullable=False),
        sa.Column("skill_match_label", sa.Integer()),
        sa.Column("experience_match_label", sa.Integer()),
        sa.Column("education_match_label", sa.Integer()),
        sa.Column("location_match_label", sa.Integer()),
        sa.Column("annotator_id", sa.String(128), nullable=False),
        sa.Column("annotation_version", sa.String(128), nullable=False),
        sa.Column("dataset_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("relevance_label BETWEEN 0 AND 3"),
        sa.UniqueConstraint("resume_id", "job_id", "annotator_id", "annotation_version", "dataset_hash"))
    for field in ("user_id", "resume_id", "job_id"):
        op.create_index(f"ix_evaluation_annotations_{field}", "evaluation_annotations", [field])


def downgrade():
    op.drop_table("evaluation_annotations")
