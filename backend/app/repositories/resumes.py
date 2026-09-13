"""Resume persistence."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume


async def get_by_checksum(session: AsyncSession, *, user_id: UUID, checksum: str) -> Resume | None:
    """The user's existing resume with these exact bytes, if any."""
    result = await session.execute(
        select(Resume).where(Resume.user_id == user_id, Resume.checksum == checksum)
    )
    return result.scalars().first()


async def create(
    session: AsyncSession,
    *,
    user_id: UUID,
    storage_key: str,
    original_filename: str,
    mime_type: str,
    checksum: str,
) -> Resume:
    resume = Resume(
        user_id=user_id,
        storage_key=storage_key,
        original_filename=original_filename,
        mime_type=mime_type,
        checksum=checksum,
    )
    session.add(resume)
    await session.flush()
    return resume


async def record_parse(
    session: AsyncSession, resume: Resume, *, parsed_text: str, parser_version: str
) -> None:
    resume.parsed_text = parsed_text
    resume.parser_version = parser_version
    await session.flush()
