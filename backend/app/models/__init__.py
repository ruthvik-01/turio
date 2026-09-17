"""ORM models.

Imported for the side effect of registering every table on `Base.metadata`,
which is what Alembic compares against.
"""

from app.models.base import Base
from app.models.application import Application, ApplicationAnswer, ApplicationEvent, ApplicationField, IdempotencyRecord, SavedAnswer
from app.models.job import Job, JobSource
from app.models.matching import Embedding, JobMatch
from app.models.profile import Profile
from app.models.profile_entities import Education, Experience, Project, Skill
from app.models.refresh_token import RefreshToken
from app.models.resume import Resume
from app.models.run import AgentRun
from app.models.rate_limit import RateLimitBucket
from app.models.evaluation import EvaluationAnnotation
from app.models.user import User

__all__ = [
    "Base",
    "AgentRun",
    "RateLimitBucket",
    "EvaluationAnnotation",
    "Application",
    "ApplicationAnswer",
    "ApplicationEvent",
    "ApplicationField",
    "IdempotencyRecord",
    "SavedAnswer",
    "Education",
    "Embedding",
    "Experience",
    "Job",
    "JobMatch",
    "JobSource",
    "Profile",
    "Project",
    "RefreshToken",
    "Resume",
    "Skill",
    "User",
]
