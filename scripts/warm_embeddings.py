"""Background pre-computation of SBERT embeddings for all eligible jobs.

Safe, idempotent, and resumable: uses content-addressed cache_key with ON CONFLICT DO NOTHING.
Run to pre-warm the database so user matching is instantaneous (<0.1s).
"""
import argparse
import asyncio
import json
import os
import sys
import time

env_json = os.path.join(os.path.dirname(__file__), "../.runtime/native/env.json")
if os.path.exists(env_json):
    with open(env_json, "r", encoding="utf-8") as f:
        env_vars = json.load(f)
    for k, v in env_vars.items():
        os.environ[k] = str(v)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.core.config import get_settings
from app.core.db import create_engine, create_session_factory
from app.ml import encoder
from app.ml.scoring import digest, job_text, load_config
from app.models.matching import Embedding
from app.repositories import jobs as job_repo
from app.repositories import matching as matching_repo
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert


async def warm_embeddings(limit: int | None = None, batch_size: int = 128):
    settings = get_settings()
    config = load_config()
    identity = [config["model_name"], config["model_revision"], config["representation_version"]]

    engine = create_engine(settings.database_url)
    factory = create_session_factory(engine)

    print("Fetching eligible jobs...")
    async with factory() as session:
        all_jobs = await job_repo.matching_jobs(session)
        if limit:
            all_jobs = all_jobs[:limit]
        total_jobs = len(all_jobs)
        print(f"Total eligible jobs to check: {total_jobs}")

        # Compute keys
        keys = [digest([identity, str(job.id), job.content_hash]) for job in all_jobs]
        cached = await matching_repo.cached_vectors(session, keys)
        missing_indices = [i for i, k in enumerate(keys) if k not in cached]
        print(f"Already cached: {len(cached)} | Missing to encode: {len(missing_indices)}")

        if not missing_indices:
            print("All job embeddings are already up to date!")
            return

        print(f"Starting SBERT encoding with batch size {batch_size}...")
        t0 = time.perf_counter()
        total_missing = len(missing_indices)
        encoded_count = 0

        for start in range(0, total_missing, batch_size):
            batch_indices = missing_indices[start:start + batch_size]
            batch_jobs = [all_jobs[i] for i in batch_indices]
            batch_texts = [job_text(job) for job in batch_jobs]
            batch_keys = [keys[i] for i in batch_indices]

            t_batch = time.perf_counter()
            vectors = await asyncio.to_thread(encoder.encode, batch_texts, config)
            t_encode = time.perf_counter() - t_batch

            values = [{"cache_key": k, "vector": v, "owner_user_id": None} for k, v in zip(batch_keys, vectors)]

            # Bulk insert
            stmt = insert(Embedding).values(values).on_conflict_do_nothing(index_elements=["cache_key"])
            await session.execute(stmt)
            await session.commit()

            encoded_count += len(values)
            elapsed = time.perf_counter() - t0
            rate = encoded_count / elapsed
            remaining = (total_missing - encoded_count) / rate if rate > 0 else 0
            print(f"[{encoded_count}/{total_missing}] ({(encoded_count/total_missing)*100:.1f}%) | "
                  f"Rate: {rate:.1f} jobs/s | Batch: {t_encode:.2f}s | ETA: {remaining/60:.1f} min", flush=True)

        print(f"Warmup complete! Encoded {encoded_count} jobs in {time.perf_counter() - t0:.1f}s.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-warm SBERT job embeddings")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of jobs to warm")
    parser.add_argument("--batch-size", type=int, default=128, help="Batch size for model encoding")
    args = parser.parse_args()

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(warm_embeddings(limit=args.limit, batch_size=args.batch_size))

