"""ORM models.

Imported for the side effect of registering every table on `Base.metadata`,
which is what Alembic compares against.
"""

from app.models.base import Base
from app.models.job import Job, JobSource
from app.models.profile import Profile
from app.models.profile_entities import Education, Experience, Project, Skill
from app.models.refresh_token import RefreshToken
from app.models.resume import Resume
from app.models.user import User

__all__ = [
    "Base",
    "Education",
    "Experience",
    "Job",
    "JobSource",
    "Profile",
    "Project",
    "RefreshToken",
    "Resume",
    "Skill",
    "User",
]
