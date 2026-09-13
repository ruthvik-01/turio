"""Profile persistence, including the entity sets that hang off a profile."""

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
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


async def get_or_create(session: AsyncSession, user_id: UUID) -> Profile:
    profile = await get_by_user_id(session, user_id)
    if profile is None:
        profile = Profile(user_id=user_id)
        session.add(profile)
        await session.flush()
    return profile


async def load_entities(session: AsyncSession, user_id: UUID) -> ProfileEntities:
    async def _all(model: type) -> list:
        result = await session.execute(select(model).where(model.user_id == user_id))
        return list(result.scalars().all())

    return ProfileEntities(
        skills=await _all(Skill),
        experiences=await _all(Experience),
        educations=await _all(Education),
        projects=await _all(Project),
    )


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
