"""Similar-turn KNN.

Given a new turn's embedding, find the K most similar past turns
in the DWH. Uses ``sklearn.neighbors.NearestNeighbors`` on the
sentence-transformer embedding space.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
from loguru import logger
from sklearn.neighbors import NearestNeighbors

from symposium.etl.transform.embedder import get_embedder


class SimilarTurnKNN:
    def __init__(self, k: int = 5) -> None:
        self.k = k
        self.nn: NearestNeighbors | None = None
        self.texts: list[str] = []
        self.meta: list[dict] = []
        self._trained = False

    def fit(self, turns: list[dict]) -> dict[str, Any]:
        """turns: list of dicts with at least 'text' key."""
        self.texts = [t["text"] for t in turns]
        self.meta = [{k: v for k, v in t.items() if k != "text"} for t in turns]
        vecs = get_embedder().encode(self.texts)
        self.nn = NearestNeighbors(
            n_neighbors=min(self.k, len(self.texts)),
            metric="cosine",
            algorithm="brute",
        )
        self.nn.fit(vecs)
        self._trained = True
        metrics = {"n_indexed": len(self.texts), "k": self.k}
        logger.info(f"[knn] fitted. {metrics}")
        return metrics

    def query(self, text: str, k: int | None = None) -> list[dict[str, Any]]:
        if not self._trained or self.nn is None:
            raise RuntimeError("KNN not fitted.")
        k = k or self.k
        vec = get_embedder().encode(text)
        distances, indices = self.nn.kneighbors(vec, n_neighbors=min(k, len(self.texts)))
        results = []
        for rank, (i, d) in enumerate(zip(indices[0], distances[0]), start=1):
            results.append({
                "rank": rank,
                "similarity": float(1.0 - d),
                "text": self.texts[int(i)],
                "meta": self.meta[int(i)],
            })
        return results

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {"nn": self.nn, "texts": self.texts, "meta": self.meta, "k": self.k},
            path,
        )

    def load(self, path: Path) -> None:
        bundle = joblib.load(path)
        self.nn = bundle["nn"]
        self.texts = bundle["texts"]
        self.meta = bundle["meta"]
        self.k = bundle["k"]
        self._trained = True
