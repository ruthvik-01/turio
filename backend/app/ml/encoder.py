"""Optional SBERT runtime. Never masquerades as a semantic model when unavailable."""

from functools import lru_cache

from app.core.config import get_settings
from app.core.errors import AppError


@lru_cache(maxsize=2)
def model(name: str, revision: str):
    settings = get_settings()
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(
            name, revision=revision, device="cpu", trust_remote_code=False,
            cache_folder=settings.model_cache_path, local_files_only=settings.model_local_files_only,
        )
    except (ImportError, OSError, ValueError) as exc:
        raise AppError("MODEL_UNAVAILABLE", "Install the ML dependencies and download the configured model before using SBERT.", 503) from exc


def encode(texts: list[str], config: dict) -> list[list[float]]:
    return model(config["model_name"], config["model_revision"]).encode(
        texts, batch_size=config["batch_size"], normalize_embeddings=True,
        show_progress_bar=False, convert_to_numpy=True,
    ).tolist()
