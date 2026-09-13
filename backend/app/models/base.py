"""Declarative base for every ORM model.

No tables are declared in Phase 0 - `users` and `refresh_tokens` arrive in
Phase 1. The base exists now so Alembic's `target_metadata` is wired to the
real project metadata from the first revision onward.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
