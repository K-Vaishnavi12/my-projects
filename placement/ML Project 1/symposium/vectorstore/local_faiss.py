"""Local FAISS backend - used when we can't reach MongoDB Atlas."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from loguru import logger

from symposium.config import get_settings
from symposium.config.personas import PERSONAS
from symposium.utils import read_pickle, write_pickle
from symposium.vectorstore.base import RetrievedChunk, VectorStore


class LocalFaissStore(VectorStore):
    """FAISS index per persona built from Mongo (or a pickled snapshot)."""

    def __init__(self) -> None:
        s = get_settings()
        self.dim = s.embedding_dim
        self.snapshot_dir = s.processed_data_dir / "faiss"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self._indexes: dict[str, Any] = {}      # persona_key -> faiss index
        self._payloads: dict[str, list[dict]] = {}

    # --------------------------------------------------------------
    # Build / load
    # --------------------------------------------------------------

    def build_from_mongo(self) -> None:
        """One-shot: read chunks from Mongo, build a FAISS index per persona."""
        import faiss
        from pymongo import MongoClient

        s = get_settings()
        client = MongoClient(s.mongodb_uri)
        db = client[s.mongodb_db]

        for pkey in list(PERSONAS.keys()) + [None]:
            coll_name = f"chunks_{pkey}" if pkey else "chunks_all"
            coll = db[coll_name]
            docs = list(coll.find(
                {},
                {"chunk_id": 1, "doc_id": 1, "doc_title": 1, "doc_url": 1,
                 "topic": 1, "text": 1, "persona_scores": 1, "embedding": 1},
            ))
            if not docs:
                logger.warning(f"[faiss] no chunks in {coll_name}, skipping")
                continue

            vectors = np.asarray([d.pop("embedding") for d in docs], dtype=np.float32)
            index = faiss.IndexFlatIP(self.dim)   # inner product = cosine (normalised)
            index.add(vectors)

            key = pkey or "__all__"
            self._indexes[key] = index
            self._payloads[key] = docs
            logger.info(f"[faiss] built index '{key}' with {len(docs)} vectors")

            faiss.write_index(index, str(self.snapshot_dir / f"{key}.faiss"))
            write_pickle(self.snapshot_dir / f"{key}.pkl", docs)

        client.close()

    def load_snapshots(self) -> None:
        import faiss

        for path in self.snapshot_dir.glob("*.faiss"):
            key = path.stem
            self._indexes[key] = faiss.read_index(str(path))
            self._payloads[key] = read_pickle(self.snapshot_dir / f"{key}.pkl")
            logger.info(f"[faiss] loaded '{key}' from snapshot")

    def _ensure_key(self, key: str) -> None:
        if key not in self._indexes:
            self.load_snapshots()
            if key not in self._indexes:
                raise RuntimeError(
                    f"FAISS index '{key}' not found. Run "
                    "`python -c \"from symposium.vectorstore.local_faiss "
                    "import LocalFaissStore; LocalFaissStore().build_from_mongo()\"` "
                    "first."
                )

    # --------------------------------------------------------------
    # Search
    # --------------------------------------------------------------

    def search(
        self,
        query_embedding: list[float],
        persona_key: str | None = None,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        key = persona_key or "__all__"
        self._ensure_key(key)

        q = np.asarray([query_embedding], dtype=np.float32)
        sims, idxs = self._indexes[key].search(q, top_k)

        results: list[RetrievedChunk] = []
        payload = self._payloads[key]
        for rank, (i, s) in enumerate(zip(idxs[0], sims[0]), start=1):
            if i < 0 or i >= len(payload):
                continue
            d = payload[int(i)]
            results.append(
                RetrievedChunk(
                    chunk_id=d["chunk_id"],
                    doc_id=d["doc_id"],
                    doc_title=d.get("doc_title", ""),
                    doc_url=d.get("doc_url"),
                    topic=d.get("topic", ""),
                    text=d["text"],
                    persona_scores=d.get("persona_scores", {}),
                    similarity=float(s),
                    rank=rank,
                )
            )
        return results
