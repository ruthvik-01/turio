"""Profile persistence, including the entity sets that hang off a profile."""

from dataclasses import dataclass, field
from datetime import date
from types import SimpleNamespace
from uuid import UUID

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.models.user import User
from app.models.profile_entities import Education, Experience, Project, Skill
from app.services.resume_parser import ParsedEducation, ParsedExperience, ParsedProject


@dataclass
class ProfileEntities:
    skills: list[Skill] = field(default_factory=list)
    experiences: list[Experience] = field(default_factory=list)
    educations: list[Education] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)


async def get_by_user_id(session: AsyncSession, user_id: UUID) -> Profile | None:
    result = await session.execute(select(Profile).where(Profile.user_id == user_id))
    return result.scalar_one_or_none()


async def get_or_create(session: AsyncSession, user_id: UUID, *, lock: bool = False) -> Profile:
    if lock:
        # Also serialize first-profile creation. Refresh any identity-map copy
        # after acquiring the lock so an older read cannot overwrite a new save.
        await session.execute(select(User.id).where(User.id == user_id).with_for_update(key_share=True))
        profile = await session.scalar(select(Profile).where(Profile.user_id == user_id)
            .with_for_update().execution_options(populate_existing=True))
    else:
        profile = await get_by_user_id(session, user_id)
    if profile is None:
        profile = Profile(user_id=user_id)
        session.add(profile)
        await session.flush()
        if not lock:
            # A read path created the row, so nothing later in this request
            # will commit it. Persist it here rather than making every caller
            # carry a transaction. Locked callers are already in a write path
            # and must keep their lock until they commit.
            await session.commit()
    return profile


async def load_entities(session: AsyncSession, user_id: UUID) -> ProfileEntities:
    if session.bind is not None and session.bind.dialect.name == "postgresql":
        return await _load_entities_batched(session, user_id)
    async def _all(model: type) -> list:
        result = await session.execute(select(model).where(model.user_id == user_id))
        return list(result.scalars().all())

    return ProfileEntities(
        skills=await _all(Skill),
        experiences=await _all(Experience),
        educations=await _all(Education),
        projects=await _all(Project),
    )


# One round trip instead of four. The database is remote, so a request that
# reads all four entity sets paid four network latencies; the queries
# themselves are trivial. `to_jsonb` keeps the row shape identical to the ORM
# objects the callers already read, and avoids four separate result mappings.
_ENTITY_QUERY = text(
    """
    SELECT 'skill' AS kind, to_jsonb(t) AS row FROM skills t WHERE t.user_id = :user_id
    UNION ALL SELECT 'experience', to_jsonb(t) FROM experiences t WHERE t.user_id = :user_id
    UNION ALL SELECT 'education', to_jsonb(t) FROM educations t WHERE t.user_id = :user_id
    UNION ALL SELECT 'project', to_jsonb(t) FROM projects t WHERE t.user_id = :user_id
    """
)


def _as_date(value):
    return date.fromisoformat(value) if isinstance(value, str) else value


async def _load_entities_batched(session: AsyncSession, user_id: UUID) -> ProfileEntities:
    """Read all four entity sets in one round trip.

    Rows come back as JSON so one query can carry four different shapes. They
    are rebuilt as plain objects rather than ORM instances: every caller reads
    them and none writes back through them.
    """
    rows = (await session.execute(_ENTITY_QUERY, {"user_id": user_id})).all()
    entities = ProfileEntities()
    for kind, row in rows:
        if kind == "skill":
            entities.skills.append(SimpleNamespace(
                name=row["name"], normalized_name=row["normalized_name"]))
        elif kind == "experience":
            entities.experiences.append(SimpleNamespace(
                company=row["company"], title=row["title"],
                start_date=_as_date(row["start_date"]), end_date=_as_date(row["end_date"]),
                description=row["description"]))
        elif kind == "education":
            entities.educations.append(SimpleNamespace(
                institution=row["institution"], degree=row["degree"], field=row["field"],
                start_date=_as_date(row["start_date"]), end_date=_as_date(row["end_date"])))
        else:
            entities.projects.append(SimpleNamespace(
                name=row["name"], description=row["description"],
                technologies=row["technologies"]))
    return entities


# Each replace_* swaps one entity set wholesale. Whole-set replacement rather
# than a diff: both extraction and user edits describe a complete correct set,
# so a merge would have to guess where a missing row went.


async def replace_skills(
    session: AsyncSession, *, user_id: UUID, names: list[str], source_resume_id: UUID | None
) -> None:
    await session.execute(delete(Skill).where(Skill.user_id == user_id))
    session.add_all(
        Skill(
            user_id=user_id,
            name=name,
            normalized_name=name.strip().lower(),
            source_resume_id=source_resume_id,
        )
        for name in names
    )
    await session.flush()


async def replace_experiences(
    session: AsyncSession,
    *,
    user_id: UUID,
    experiences: list[ParsedExperience],
    source_resume_id: UUID | None,
) -> None:
    await session.execute(delete(Experience).where(Experience.user_id == user_id))
    session.add_all(
        Experience(
            user_id=user_id,
            company=item.company,
            title=item.title,
            start_date=item.start_date,
            end_date=item.end_date,
            description=item.description,
            source_resume_id=source_resume_id,
        )
        for item in experiences
    )
    await session.flush()


async def replace_educations(
    session: AsyncSession,
    *,
    user_id: UUID,
    educations: list[ParsedEducation],
    source_resume_id: UUID | None,
) -> None:
    await session.execute(delete(Education).where(Education.user_id == user_id))
    session.add_all(
        Education(
            user_id=user_id,
            institution=item.institution,
            degree=item.degree,
            field=item.field,
            start_date=item.start_date,
            end_date=item.end_date,
            source_resume_id=source_resume_id,
        )
        for item in educations
    )
    await session.flush()


async def replace_projects(
    session: AsyncSession,
    *,
    user_id: UUID,
    projects: list[ParsedProject],
    source_resume_id: UUID | None,
) -> None:
    await session.execute(delete(Project).where(Project.user_id == user_id))
    session.add_all(
        Project(
            user_id=user_id,
            name=item.name,
            description=item.description,
            technologies=item.technologies,
            source_resume_id=source_resume_id,
        )
        for item in projects
    )
    await session.flush()
