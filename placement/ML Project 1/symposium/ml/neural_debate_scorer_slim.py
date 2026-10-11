"""Compatibility shim for Streamlit Cloud (no TensorFlow).

Replaces the Keras MLP with a scikit-learn ``MLPClassifier`` so we don't
need to ship TensorFlow's ~500 MB footprint. Same public interface as
the original :class:`NeuralDebateScorer` so no other code needs to change.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler


FEATURE_COLS = [
    "avg_historian",
    "avg_scientist",
    "avg_poet",
    "avg_skeptic",
    "avg_child",
    "turns",
    "std_across",
    "mean_across",
]
LABELS = ["low", "medium", "high"]


class NeuralDebateScorer:
    """Sklearn MLP masquerading as a Keras model (same API)."""

    def __init__(self) -> None:
        self.scaler = StandardScaler()
        self.model: MLPClassifier | None = None
        self._trained = False
        self._label_index = {l: i for i, l in enumerate(LABELS)}

    def train(self, df: pd.DataFrame, epochs: int = 30) -> dict[str, Any]:
        X = df[FEATURE_COLS].to_numpy(dtype=np.float32)
        y = np.asarray([self._label_index[l] for l in df["label"]], dtype=np.int64)

        rng = np.random.default_rng(42)
        idx = rng.permutation(len(X))
        cut = int(0.8 * len(X))
        train_idx, test_idx = idx[:cut], idx[cut:]

        X_train = self.scaler.fit_transform(X[train_idx])
        X_test = self.scaler.transform(X[test_idx])

        self.model = MLPClassifier(
            hidden_layer_sizes=(32, 16),
            activation="relu",
            solver="adam",
            learning_rate_init=1e-3,
            max_iter=epochs * 10,
            random_state=42,
        )
        self.model.fit(X_train, y[train_idx])
        acc = float(self.model.score(X_test, y[test_idx]))
        train_acc = float(self.model.score(X_train, y[train_idx]))

        self._trained = True
        metrics = {
            "test_accuracy": round(acc, 4),
            "test_loss": round(1.0 - acc, 4),
            "epochs": epochs,
            "n_train": int(len(train_idx)),
            "n_test": int(len(test_idx)),
            "final_train_acc": round(train_acc, 4),
        }
        logger.info(f"[nn-slim] trained. {metrics}")
        return metrics

    def predict(self, features: dict | list[dict]) -> list[dict[str, Any]]:
        if not self._trained or self.model is None:
            raise RuntimeError("Neural net not trained.")
        rows = [features] if isinstance(features, dict) else features
        X = np.asarray(
            [[r.get(c, 0.0) for c in FEATURE_COLS] for r in rows],
            dtype=np.float32,
        )
        X = self.scaler.transform(X)
        probs = self.model.predict_proba(X)
        out = []
        for i, r in enumerate(rows):
            idx = int(np.argmax(probs[i]))
            out.append({
                "label": LABELS[idx],
                "score": float(probs[i, idx]),
                "probs": {LABELS[j]: float(probs[i, j]) for j in range(len(LABELS))},
            })
        return out

    def save(self, path: Path) -> None:
        if self.model is None:
            raise RuntimeError("Nothing to save.")
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"scaler": self.scaler, "model": self.model}, path)

    def load(self, path: Path) -> None:
        bundle = joblib.load(path)
        self.scaler = bundle["scaler"]
        self.model = bundle["model"]
        self._trained = True
