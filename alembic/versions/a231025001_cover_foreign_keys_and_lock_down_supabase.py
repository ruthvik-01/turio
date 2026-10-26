"""Cover remaining foreign keys and lock down Supabase client access.

Two changes, both idempotent so this revision is safe on an existing database:

1. Six foreign keys had no covering index. Deleting a parent row (a resume, a
   user's refresh token) made PostgreSQL sequentially scan the child table to
   enforce the constraint. Names follow the existing ix_<table>_<column>
   convention.

2. Supabase grants the `anon` and `authenticated` PostgREST roles full access
   to every table in `public` by default. Turio's API talks to PostgreSQL
   directly as its own role and never uses PostgREST, so those grants are pure
   exposure: anyone holding the publishable key could read every row. Revoking
   them and enabling RLS with no policies denies by default. The table owner
   (the backend's role) is unaffected because RLS is not FORCEd.

   The role grants are guarded: plain PostgreSQL installations have no `anon`
   or `authenticated` role, and REVOKE from a missing role is an error.

Revision ID: a231025001
Revises: a231013001
"""

from alembic import op

revision = "a231025001"
down_revision = "a231013001"
branch_labels = None
depends_on = None

# Foreign keys the earlier revisions indexed inconsistently.
_COVERING_INDEXES = (
    ("applications", "resume_id"),
    ("educations", "source_resume_id"),
    ("experiences", "source_resume_id"),
    ("projects", "source_resume_id"),
    ("refresh_tokens", "replaced_by_token_id"),
    ("skills", "source_resume_id"),
)

# Tables in the schema that Supabase exposes through PostgREST.
_PUBLIC_TABLES = (
    "agent_runs",
    "alembic_version",
    "application_answers",
    "application_events",
    "application_fields",
    "applications",
    "educations",
    "embeddings",
    "evaluation_annotations",
    "experiences",
    "idempotency_records",
    "job_matches",
    "job_sources",
    "jobs",
    "profiles",
    "projects",
    "rate_limit_buckets",
    "refresh_tokens",
    "resumes",
    "saved_answers",
    "skills",
    "users",
)


def upgrade() -> None:
    for table, column in _COVERING_INDEXES:
        op.execute(
            f"CREATE INDEX IF NOT EXISTS ix_{table}_{column} ON {table} ({column})"
        )

    # Only Supabase defines these roles. Guard so a plain PostgreSQL database
    # (the native development runtime) runs this revision unchanged.
    op.execute(
        """
        DO $$
        DECLARE
            t text;
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon')
               OR NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                RETURN;
            END IF;

            FOREACH t IN ARRAY ARRAY[%s]
            LOOP
                EXECUTE format('REVOKE ALL ON TABLE public.%%I FROM anon, authenticated', t);
                EXECUTE format('ALTER TABLE public.%%I ENABLE ROW LEVEL SECURITY', t);
            END LOOP;

            REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
            REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM anon, authenticated;

            ALTER DEFAULT PRIVILEGES IN SCHEMA public
                REVOKE ALL ON TABLES FROM anon, authenticated;
            ALTER DEFAULT PRIVILEGES IN SCHEMA public
                REVOKE ALL ON SEQUENCES FROM anon, authenticated;
            ALTER DEFAULT PRIVILEGES IN SCHEMA public
                REVOKE ALL ON FUNCTIONS FROM anon, authenticated;
        END
        $$"""
        % ", ".join(f"'{name}'" for name in _PUBLIC_TABLES)
    )


def downgrade() -> None:
    for table, column in _COVERING_INDEXES:
        op.execute(f"DROP INDEX IF EXISTS ix_{table}_{column}")

    # RLS and the revoked grants are deliberately not restored: re-opening the
    # tables to the anon key is never the desired outcome of a rollback.
