"""Factory that returns the configured vector store singleton."""

from __future__ import annotations

from functools import lru_cache

from symposium.config import get_settings
from symposium.vectorstore.base import VectorStore


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    s = get_settings()
    if s.use_local_vector_store:
        from symposium.vectorstore.local_faiss import LocalFaissStore
        return LocalFaissStore()
    from symposium.vectorstore.mongo_store import MongoAtlasStore
    return MongoAtlasStore()
