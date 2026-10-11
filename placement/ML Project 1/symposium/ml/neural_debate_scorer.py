"""Neural network debate-outcome scorer.

Small Keras MLP that predicts whether a debate ends with **high /
medium / low consensus** given aggregated per-persona features.

**Deployment-friendly fallback**: if TensorFlow isn't installed
(e.g. on Streamlit Cloud where memory is tight), this module
transparently swaps in a scikit-learn ``MLPClassifier`` with the same
public API. Same file name, same import path, same class name.
"""

from __future__ import annotations

# --- Try TF first; fall back to sklearn if not available ----------
try:
    import tensorflow  # noqa: F401
    _HAS_TF = True
except ImportError:
    _HAS_TF = False


# =====================================================================
# Fallback: pure-sklearn implementation for slim deployments
# =====================================================================
if not _HAS_TF:
    from symposium.ml.neural_debate_scorer_slim import (
        FEATURE_COLS,
        LABELS,
        NeuralDebateScorer,
    )
    __all__ = ["FEATURE_COLS", "LABELS", "NeuralDebateScorer"]

else:
    # =================================================================
    # Full TensorFlow / Keras implementation
    # =================================================================
    from pathlib import Path
    from typing import Any

    import numpy as np
    import pandas as pd
    from loguru import logger

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
        def __init__(self) -> None:
            self.model = None
            self._trained = False
            self._label_index: dict[str, int] = {l: i for i, l in enumerate(LABELS)}

        def _build(self, input_dim: int) -> Any:
            try:
                from tensorflow.keras import layers, models  # type: ignore
                from tensorflow.keras.optimizers import Adam  # type: ignore
            except ModuleNotFoundError:
                from keras import layers, models  # type: ignore
                from keras.optimizers import Adam  # type: ignore

            m = models.Sequential(
                [
                    layers.Input(shape=(input_dim,)),
                    layers.Dense(32, activation="relu"),
                    layers.Dropout(0.1),
                    layers.Dense(16, activation="relu"),
                    layers.Dense(len(LABELS), activation="softmax"),
                ]
            )
            m.compile(
                optimizer=Adam(learning_rate=1e-3),
                loss="sparse_categorical_crossentropy",
                metrics=["accuracy"],
            )
            return m

        def train(self, df: pd.DataFrame, epochs: int = 30) -> dict[str, Any]:
            X = df[FEATURE_COLS].to_numpy(dtype=np.float32)
            y = np.asarray([self._label_index[l] for l in df["label"]], dtype=np.int64)

            rng = np.random.default_rng(42)
            idx = rng.permutation(len(X))
            cut = int(0.8 * len(X))
            train_idx, test_idx = idx[:cut], idx[cut:]

            self.model = self._build(X.shape[1])
            history = self.model.fit(
                X[train_idx], y[train_idx],
                validation_data=(X[test_idx], y[test_idx]),
                epochs=epochs,
                batch_size=32,
                verbose=0,
            )
            loss, acc = self.model.evaluate(X[test_idx], y[test_idx], verbose=0)
            self._trained = True
            metrics = {
                "test_accuracy": round(float(acc), 4),
                "test_loss": round(float(loss), 4),
                "epochs": epochs,
                "n_train": int(len(train_idx)),
                "n_test": int(len(test_idx)),
                "final_train_acc": round(float(history.history["accuracy"][-1]), 4),
            }
            logger.info(f"[nn] trained. {metrics}")
            return metrics

        def predict(self, features: dict | list[dict]) -> list[dict[str, Any]]:
            if not self._trained or self.model is None:
                raise RuntimeError("Neural net not trained.")
            rows = [features] if isinstance(features, dict) else features
            X = np.asarray(
                [[r.get(c, 0.0) for c in FEATURE_COLS] for r in rows],
                dtype=np.float32,
            )
            probs = self.model.predict(X, verbose=0)
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
            self.model.save(str(path))

        def load(self, path: Path) -> None:
            try:
                from tensorflow.keras.models import load_model  # type: ignore
            except ModuleNotFoundError:
                from keras.models import load_model  # type: ignore
            self.model = load_model(str(path))
            self._trained = True

    __all__ = ["FEATURE_COLS", "LABELS", "NeuralDebateScorer"]
