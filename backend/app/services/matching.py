"""Generate reproducible, labeled recommendations with invalidation evidence."""

import asyncio
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.time import utcnow
from app.ml import encoder
from app.ml.scoring import baseline_scores, candidate_text, cosine, digest, job_text, load_config, structured_evidence
from app.models.matching import JobMatch
from app.models.profile import Profile
from app.repositories import jobs as job_repo
from app.repositories import matching as repo
from app.schemas.matching import MatchData, MatchPage
from app.services.jobs import to_job_data
from app.services.profile import get_profile, get_profile_version


def config_identity(config: dict) -> str:
    # Experience intervals ending "Present" depend on the current month.
    return digest([config, utcnow().date().strftime("%Y-%m")])


async def semantic_scores(session, user_id, profile, jobs, config) -> list[float]:
    import numpy as np

    identity = [config["model_name"], config["model_revision"], config["representation_version"]]
    texts = [candidate_text(profile)] + [job_text(job) for job in jobs]
    keys = [digest([identity, str(user_id), profile.version, texts[0]])]
    keys += [digest([identity, str(job.id), job.content_hash]) for job in jobs]
    cached = await repo.cached_vectors(session, keys)
    missing = [index for index, key in enumerate(keys) if key not in cached]
    buffered_values = []
    for start in range(0, len(missing), config["batch_size"]):
        batch = missing[start:start + config["batch_size"]]
        vectors = await asyncio.to_thread(encoder.encode, [texts[index] for index in batch], config)
        values = [{"cache_key": keys[index], "vector": vector, "owner_user_id": user_id if index == 0 else None} for index, vector in zip(batch, vectors)]
        buffered_values.extend(values)
        cached.update({v["cache_key"]: v["vector"] for v in values})
        if len(buffered_values) >= 200:
            await repo.store_vectors(session, buffered_values)
            buffered_values = []
    if buffered_values:
        await repo.store_vectors(session, buffered_values)

    candidate_vec = np.array(cached[keys[0]], dtype=np.float32)
    job_matrix = np.array([cached[key] for key in keys[1:]], dtype=np.float32)
    c_norm = np.linalg.norm(candidate_vec)
    if c_norm > 0:
        candidate_vec /= c_norm
    j_norms = np.linalg.norm(job_matrix, axis=1, keepdims=True)
    j_norms[j_norms == 0] = 1.0
    job_matrix /= j_norms
    return np.dot(job_matrix, candidate_vec).clip(0.0, 1.0).tolist()


def to_data(row, job) -> MatchData:
    return MatchData(id=row.id, job=to_job_data(job), method=row.method, model_name=row.model_name,
                     model_version=row.model_version, ranking_config_version=row.ranking_config_version,
                     profile_version=row.profile_version, final_score=row.final_score,
                     explanation=row.explanation_payload, created_at=row.created_at)


async def generate(session: AsyncSession, user_id: UUID, method: str = "sbert", *, checkpoint=None) -> MatchPage:
    profile = await get_profile(session, user_id=user_id)
    if not candidate_text(profile).strip():
        raise AppError("MISSING_REQUIRED_FIELD", "Add skills, experience or preferred roles before matching.", 422)
    await repo.lock_user(session, user_id)
    config = load_config()
    fingerprint = await job_repo.inventory_fingerprint(session)
    current = await repo.user_matches(session, user_id, method)
    signature = config_identity(config)
    if current and all(row.profile_version == profile.version and row.inventory_hash == fingerprint and row.ranking_config_version == signature for row in current):
        return await list_matches(session, user_id, method)
    jobs = await job_repo.matching_jobs(session)
    if method == "sbert":
        scores = await semantic_scores(session, user_id, profile, jobs, config) if jobs else []
    else:
        scores = await asyncio.to_thread(baseline_scores, candidate_text(profile), [job_text(job) for job in jobs], method)
    rows = []
    for job, semantic in zip(jobs, scores):
        final, evidence = structured_evidence(profile, job, semantic, config, utcnow().date())
        evidence["method"] = method
        evidence["weights"] = config["weights"]
        rows.append(JobMatch(user_id=user_id, job_id=job.id, method=method,
            model_name=config["model_name"] if method == "sbert" else f"{method}-baseline",
            model_version=config["model_revision"] if method == "sbert" else "v1",
            ranking_config_version=signature, inventory_hash=fingerprint, profile_version=profile.version,
            job_hash=job.content_hash, final_score=final, explanation_payload=evidence))
    version_now = await session.scalar(select(Profile.version).where(Profile.user_id == user_id))
    if version_now != profile.version or await job_repo.inventory_fingerprint(session) != fingerprint:
        await session.rollback()
        raise AppError("CONFLICT", "The profile or inventory changed during matching. Please retry.", 409)
    if checkpoint:
        await checkpoint()
    await repo.replace_matches(session, user_id, method, rows)
    await session.commit()
    return await list_matches(session, user_id, method)


async def list_matches(session: AsyncSession, user_id: UUID, method: str, limit: int = 20, offset: int = 0) -> MatchPage:
    profile_version = await get_profile_version(session, user_id=user_id)
    fingerprint = await job_repo.inventory_fingerprint(session)
    signature = config_identity(load_config())
    rows, total, stale = await repo.match_page(session, user_id, method, profile_version, fingerprint, signature, limit, offset)
    return MatchPage(matches=[to_data(row, job) for row, job in rows], total=total,
                     limit=limit, offset=offset, method=method, stale=stale)


async def detail(session: AsyncSession, user_id: UUID, match_id: UUID) -> MatchData:
    row = await repo.owned_match(session, user_id, match_id)
    if row is None:
        raise AppError("NOT_FOUND", "No match with that id.", 404)
    profile_version = await get_profile_version(session, user_id=user_id)
    if row.profile_version != profile_version or row.inventory_hash != await job_repo.inventory_fingerprint(session) or row.ranking_config_version != config_identity(load_config()):
        raise AppError("CONFLICT", "This recommendation is stale. Refresh your matches.", 409)
    return to_data(row, await job_repo.get_by_id(session, row.job_id))
