"""Source-backed supplemental resume facts; login email remains unchanged."""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "a231013001"
down_revision = "a230916001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("profiles", sa.Column("contact_email", sa.String(255), nullable=True))
    op.add_column("profiles", sa.Column("summary", sa.Text(), nullable=True))
    for name in ("certifications", "achievements"):
        op.add_column("profiles", sa.Column(name, sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=True))


def downgrade():
    # Runtime rollback retains the columns and candidate data; destructive
    # downgrades are only for disposable test databases.
    for name in ("achievements", "certifications", "summary", "contact_email"):
        op.drop_column("profiles", name)
