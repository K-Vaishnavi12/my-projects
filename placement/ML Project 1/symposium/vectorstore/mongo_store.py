"""MongoDB Atlas Vector Search backend."""

from __future__ import annotations

from typing import Any

from loguru import logger
from pymongo import MongoClient

from symposium.config import get_settings
from symposium.config.personas import PERSONAS
from symposium.vectorstore.base import RetrievedChunk, VectorStore


class MongoAtlasStore(VectorStore):
    """Uses the ``$vectorSearch`` aggregation stage.

    Falls back to a cosine-similarity computation *client-side* if the
    Atlas Search index isn't ready yet (useful during first-run demos).
    """

    INDEX_NAME = "vector_index"

    def __init__(self) -> None:
        s = get_settings()
        self.client = MongoClient(s.mongodb_uri)
        self.db = self.client[s.mongodb_db]

    def _collection_name(self, persona_key: str | None) -> str:
        if persona_key is None:
            return "chunks_all"
        if persona_key not in PERSONAS:
            raise KeyError(f"Unknown persona {persona_key}")
        return f"chunks_{persona_key}"

    def search(
        self,
        query_embedding: list[float],
        persona_key: str | None = None,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        coll_name = self._collection_name(persona_key)
        coll = self.db[coll_name]

        try:
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": self.INDEX_NAME,
                        "path": "embedding",
                        "queryVector": query_embedding,
                        "numCandidates": max(top_k * 10, 50),
                        "limit": top_k,
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "chunk_id": 1,
                        "doc_id": 1,
                        "doc_title": 1,
                        "doc_url": 1,
                        "topic": 1,
                        "text": 1,
                        "persona_scores": 1,
                        "similarity": {"$meta": "vectorSearchScore"},
                    }
                },
            ]
            docs = list(coll.aggregate(pipeline))
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                f"[vs] $vectorSearch failed ({exc}); "
                "falling back to client-side cosine (slow)."
            )
            docs = self._fallback_cosine(coll_name, query_embedding, top_k)

        return [
            RetrievedChunk(
                chunk_id=d["chunk_id"],
                doc_id=d["doc_id"],
                doc_title=d.get("doc_title", ""),
                doc_url=d.get("doc_url"),
                topic=d.get("topic", ""),
                text=d["text"],
                persona_scores=d.get("persona_scores", {}),
                similarity=float(d.get("similarity", 0.0)),
                rank=i + 1,
            )
            for i, d in enumerate(docs)
        ]

    # --------------------------------------------------------------
    # Fallback: brute-force cosine using numpy. Only used when Atlas
    # index is missing (first run, or non-Atlas MongoDB).
    # --------------------------------------------------------------

    def _fallback_cosine(
        self,
        coll_name: str,
        query_embedding: list[float],
        top_k: int,
    ) -> list[dict[str, Any]]:
        import numpy as np

        q = np.asarray(query_embedding, dtype=np.float32)
        # (embeddings are normalised at ingest, so dot == cosine)
        cursor = self.db[coll_name].find(
            {},
            {"chunk_id": 1, "doc_id": 1, "doc_title": 1, "doc_url": 1,
             "topic": 1, "text": 1, "persona_scores": 1, "embedding": 1},
        )
        scored: list[tuple[float, dict]] = []
        for d in cursor:
            emb = np.asarray(d.pop("embedding"), dtype=np.float32)
            sim = float(np.dot(emb, q))
            d["similarity"] = sim
            scored.append((sim, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in scored[:top_k]]

    def close(self) -> None:
        self.client.close()
