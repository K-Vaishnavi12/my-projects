"""K-Means clustering + PCA visualisation of argument space.

Given a bag of turn/chunk texts, produce:
- ``k`` clusters (K-Means)
- 2D PCA projection for the Analytics page
- Silhouette metric so we can pick a good k
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
from loguru import logger
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

from symposium.etl.transform.embedder import get_embedder


class ArgumentClusterer:
    def __init__(self, k: int = 5, random_state: int = 42) -> None:
        self.k = k
        self.random_state = random_state
        self.kmeans: KMeans | None = None
        self.pca: PCA | None = None
        self._embeddings: np.ndarray | None = None
        self._texts: list[str] = []
        self._trained = False

    def fit(self, texts: list[str]) -> dict[str, Any]:
        vecs = get_embedder().encode(texts)
        self._embeddings = vecs
        self._texts = list(texts)

        self.kmeans = KMeans(n_clusters=self.k, random_state=self.random_state, n_init=10)
        labels = self.kmeans.fit_predict(vecs)

        sil = float(silhouette_score(vecs, labels)) if len(set(labels)) > 1 else 0.0

        self.pca = PCA(n_components=2, random_state=self.random_state)
        self.pca.fit(vecs)

        self._trained = True
        metrics = {
            "k": self.k,
            "n_samples": len(texts),
            "silhouette": round(sil, 4),
            "pca_explained_variance": [round(v, 4) for v in self.pca.explained_variance_ratio_],
        }
        logger.info(f"[cluster] fitted. {metrics}")
        return metrics

    def project(self, texts: list[str] | None = None) -> tuple[np.ndarray, np.ndarray]:
        """Return (xy_2d, cluster_labels) for either the training set
        or a new batch of texts."""
        if not self._trained or self.kmeans is None or self.pca is None:
            raise RuntimeError("Not fitted.")
        if texts is None:
            vecs = self._embeddings
        else:
            vecs = get_embedder().encode(texts)
        assert vecs is not None
        xy = self.pca.transform(vecs)
        labels = self.kmeans.predict(vecs)
        return xy, labels

    def top_terms_per_cluster(self, top_n: int = 6) -> dict[int, list[str]]:
        """Cheap keyword summary using centroid nearest samples."""
        if not self._trained or self.kmeans is None:
            raise RuntimeError("Not fitted.")
        assert self._embeddings is not None
        out: dict[int, list[str]] = {}
        for cid in range(self.k):
            mask = self.kmeans.labels_ == cid
            if not mask.any():
                out[cid] = []
                continue
            centroid = self.kmeans.cluster_centers_[cid]
            in_cluster = self._embeddings[mask]
            in_cluster_texts = [t for t, m in zip(self._texts, mask) if m]
            sims = in_cluster @ centroid
            top_idx = np.argsort(-sims)[:top_n]
            out[cid] = [in_cluster_texts[i][:120] for i in top_idx]
        return out

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "k": self.k,
                "kmeans": self.kmeans,
                "pca": self.pca,
                "texts": self._texts,
                "embeddings": self._embeddings,
            },
            path,
        )

    def load(self, path: Path) -> None:
        bundle = joblib.load(path)
        self.k = bundle["k"]
        self.kmeans = bundle["kmeans"]
        self.pca = bundle["pca"]
        self._texts = bundle["texts"]
        self._embeddings = bundle["embeddings"]
        self._trained = True
