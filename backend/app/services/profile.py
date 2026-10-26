"""Profile reads and user-confirmed updates (API_SPEC.md section 3)."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.core.errors import AppError
from app.repositories import profiles as profile_repo
from app.repositories.profiles import ProfileEntities
from app.schemas.profile import (
    EducationData,
    ExperienceData,
    ProfileUpdateRequest,
    ProfileWithEntities,
    ProjectData,
    SkillData,
)
from app.services.resume_parser import ParsedEducation, ParsedExperience, ParsedProject

logger = logging.getLogger(__name__)

_ENTITY_FIELDS = frozenset({"skills", "experiences", "educations", "projects"})


def to_profile_data(profile: Profile, entities: ProfileEntities) -> ProfileWithEntities:
    return ProfileWithEntities(
        id=profile.id,
        version=profile.version,
        full_name=profile.full_name,
        contact_email=profile.contact_email,
        summary=profile.summary,
        certifications=profile.certifications,
        achievements=profile.achievements,
        phone=profile.phone,
        location=profile.location,
        preferred_roles=profile.preferred_roles,
        linkedin_url=profile.linkedin_url,
        github_url=profile.github_url,
        portfolio_url=profile.portfolio_url,
        work_authorization_status=profile.work_authorization_status,
        sponsorship_required=profile.sponsorship_required,
        updated_at=profile.updated_at,
        skills=[
            SkillData(name=item.name, normalized_name=item.normalized_name)
            for item in entities.skills
        ],
        experiences=[
            ExperienceData(
                company=item.company,
                title=item.title,
                start_date=item.start_date,
                end_date=item.end_date,
                description=item.description,
            )
            for item in entities.experiences
        ],
        educations=[
            EducationData(
                institution=item.institution,
                degree=item.degree,
                field=item.field,
                start_date=item.start_date,
                end_date=item.end_date,
            )
            for item in entities.educations
        ],
        projects=[
            ProjectData(
                name=item.name,
                description=item.description,
                technologies=item.technologies or [],
            )
            for item in entities.projects
        ],
    )


async def get_profile(session: AsyncSession, *, user_id) -> ProfileWithEntities:
    profile = await profile_repo.get_or_create(session, user_id)
    entities = await profile_repo.load_entities(session, user_id)
    return to_profile_data(profile, entities)


async def get_profile_version(session: AsyncSession, *, user_id) -> int:
    """Just the version, for callers that only compare it.

    `get_profile` loads four entity sets and commits; ranking and match
    staleness checks need the version alone and were paying for all of it.
    """
    profile = await profile_repo.get_or_create(session, user_id)
    await session.commit()
    return profile.version


async def update_profile(
    session: AsyncSession, *, user_id, payload: ProfileUpdateRequest
) -> ProfileWithEntities:
    """Apply a user's corrections.

    These values are what later phases read: extraction only ever seeds them.
    """
    profile = await profile_repo.get_or_create(session, user_id, lock=True)
    if payload.expected_profile_version is not None and payload.expected_profile_version != profile.version:
        await session.rollback()
        raise AppError("CONFLICT", "Your profile changed. Reload it before saving these suggestions.", 409)
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_profile_version", None)

    for name, value in changes.items():
        if name not in _ENTITY_FIELDS:
            setattr(profile, name, value)

    # Rows the user submits are authored by the user, so they carry no resume
    # provenance. Extraction is the only source that sets source_resume_id.
    if "skills" in changes:
        await profile_repo.replace_skills(
            session, user_id=user_id, names=changes["skills"], source_resume_id=None
        )
    if "experiences" in changes:
        await profile_repo.replace_experiences(
            session,
            user_id=user_id,
            experiences=[
                ParsedExperience(**item.model_dump()) for item in payload.experiences or []
            ],
            source_resume_id=None,
        )
    if "educations" in changes:
        await profile_repo.replace_educations(
            session,
            user_id=user_id,
            educations=[ParsedEducation(**item.model_dump()) for item in payload.educations or []],
            source_resume_id=None,
        )
    if "projects" in changes:
        await profile_repo.replace_projects(
            session,
            user_id=user_id,
            projects=[
                ParsedProject(
                    name=item.name,
                    description=item.description,
                    technologies=item.technologies,
                )
                for item in payload.projects or []
            ],
            source_resume_id=None,
        )

    # Cached matching and mapping key off this, so it must change whenever the
    # profile does (ADR-019).
    profile.version += 1
    await session.flush()

    entities = await profile_repo.load_entities(session, user_id)
    await session.commit()

    logger.info(
        "profile_updated",
        extra={
            "extra_fields": {
                "user_id": str(user_id),
                "profile_version": profile.version,
                "fields": sorted(changes),
            }
        },
    )
    return to_profile_data(profile, entities)
