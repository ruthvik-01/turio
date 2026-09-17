"""Source-backed nullable job deadlines and company logos."""
import sqlalchemy as sa
from alembic import op

revision = "a230916001"
down_revision = "f192dea57304"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("jobs", sa.Column("application_deadline", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("company_logo_url", sa.Text(), nullable=True))
    op.create_index("ix_jobs_application_deadline", "jobs", ["application_deadline"])


def downgrade():
    op.drop_index("ix_jobs_application_deadline", table_name="jobs")
    op.drop_column("jobs", "company_logo_url")
    op.drop_column("jobs", "application_deadline")
