"""Embedder: cached sentence-transformers wrapper.

Uses ``sentence-transformers/all-MiniLM-L6-v2`` by default (384-dim).
Model is loaded lazily and reused across calls so ETL doesn't pay the
warmup cost repeatedly.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Iterable

import numpy as np
from loguru import logger

from symposium.config import get_settings


class Embedder:
    """Thin wrapper around sentence-transformers for stable typing."""

    def __init__(self, model_name: str | None = None) -> None:
        s = get_settings()
        self.model_name = model_name or s.embedding_model
        self._model = None  # lazy

    def _ensure(self) -> None:
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # local import - heavy
            logger.info(f"[embedder] loading {self.model_name} ...")
            self._model = SentenceTransformer(self.model_name)

    def encode(self, texts: str | Iterable[str], batch_size: int = 32) -> np.ndarray:
        self._ensure()
        assert self._model is not None
        if isinstance(texts, str):
            texts = [texts]
        else:
            texts = list(texts)
        return np.asarray(
            self._model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            ),
            dtype=np.float32,
        )


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    """Module-level singleton so we load MiniLM exactly once."""
    return Embedder()
