"""Agreement regressor.

Predicts a continuous 'agrees with prior turn' score in [0, 1] using
Ridge Regression on TF-IDF features. Also exposes a Logistic
Regression 'high vs low agreement' binary classifier for comparison
(covers both **Linear** and **Logistic** regression from the syllabus).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
from loguru import logger
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


class AgreementRegressor:
    def __init__(self) -> None:
        self.reg = Pipeline(
            steps=[
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2,
                                          stop_words="english")),
                ("ridge", Ridge(alpha=1.0)),
            ]
        )
        self.clf = Pipeline(
            steps=[
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2,
                                          stop_words="english")),
                ("logit", LogisticRegression(max_iter=1000)),
            ]
        )
        self._trained = False

    def train(self, X_text: list[str], y_score: list[float]) -> dict[str, Any]:
        y_arr = np.asarray(y_score, dtype=float)
        X_tr, X_te, y_tr, y_te = train_test_split(
            X_text, y_arr, test_size=0.2, random_state=42
        )
        self.reg.fit(X_tr, y_tr)
        preds = self.reg.predict(X_te)
        r2 = r2_score(y_te, preds)
        mae = mean_absolute_error(y_te, preds)

        # binary companion
        y_bin = (y_arr >= 0.5).astype(int)
        Xb_tr, Xb_te, yb_tr, yb_te = train_test_split(
            X_text, y_bin, test_size=0.2, stratify=y_bin, random_state=42
        )
        self.clf.fit(Xb_tr, yb_tr)
        acc = float(np.mean(self.clf.predict(Xb_te) == yb_te))

        metrics = {
            "ridge_r2": round(float(r2), 4),
            "ridge_mae": round(float(mae), 4),
            "logit_accuracy": round(acc, 4),
            "n_train": len(X_tr),
            "n_test": len(X_te),
        }
        self._trained = True
        logger.info(f"[agreement] trained. metrics={metrics}")
        return metrics

    def predict(self, texts: list[str]) -> np.ndarray:
        if not self._trained:
            raise RuntimeError("Model not trained.")
        preds = self.reg.predict(texts)
        return np.clip(preds, 0.0, 1.0)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"reg": self.reg, "clf": self.clf}, path)

    def load(self, path: Path) -> None:
        bundle = joblib.load(path)
        self.reg = bundle["reg"]
        self.clf = bundle["clf"]
        self._trained = True
