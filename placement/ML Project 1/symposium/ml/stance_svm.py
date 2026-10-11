"""Stance classifier - Support Vector Machine.

Classifies a piece of text (agent turn) as ``agree`` / ``disagree`` /
``neutral`` w.r.t. the prior turn.

Pipeline: TF-IDF -> LinearSVC. LinearSVC scales to thousands of
samples in seconds and is a textbook SVM implementation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
from loguru import logger
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC


class StanceSVM:
    LABELS = ("agree", "disagree", "neutral")

    def __init__(self) -> None:
        base = LinearSVC(C=1.0, class_weight="balanced")
        # wrap in calibrator so we get probabilities for the UI
        self.model = Pipeline(
            steps=[
                (
                    "tfidf",
                    TfidfVectorizer(
                        ngram_range=(1, 2),
                        max_features=20_000,
                        min_df=2,
                        stop_words="english",
                    ),
                ),
                (
                    "clf",
                    CalibratedClassifierCV(base, cv=3),
                ),
            ]
        )
        self._trained = False

    # --------------------------------------------------------------
    # Train / evaluate
    # --------------------------------------------------------------

    def train(self, X_text: list[str], y: list[str]) -> dict[str, Any]:
        X_tr, X_te, y_tr, y_te = train_test_split(
            X_text, y, test_size=0.2, stratify=y, random_state=42
        )
        self.model.fit(X_tr, y_tr)
        preds = self.model.predict(X_te)
        report = classification_report(y_te, preds, output_dict=True, zero_division=0)
        metrics = {
            "accuracy": round(accuracy_score(y_te, preds), 4),
            "f1_macro": round(f1_score(y_te, preds, average="macro"), 4),
            "n_train": len(X_tr),
            "n_test": len(X_te),
            "per_class": {
                lbl: {
                    "precision": round(report[lbl]["precision"], 4),
                    "recall":    round(report[lbl]["recall"], 4),
                    "f1":        round(report[lbl]["f1-score"], 4),
                    "support":   int(report[lbl]["support"]),
                }
                for lbl in self.LABELS if lbl in report
            },
        }
        self._trained = True
        logger.info(f"[stance_svm] trained. metrics={metrics}")
        return metrics

    # --------------------------------------------------------------
    # Predict
    # --------------------------------------------------------------

    def predict(self, texts: list[str]) -> list[dict[str, Any]]:
        if not self._trained:
            raise RuntimeError("Model not trained. Call train() or load() first.")
        probs = self.model.predict_proba(texts)
        classes = self.model.named_steps["clf"].classes_
        out = []
        for i, text in enumerate(texts):
            best_idx = int(np.argmax(probs[i]))
            out.append({
                "text": text,
                "label": classes[best_idx],
                "score": float(probs[i, best_idx]),
                "probs": {c: float(probs[i, j]) for j, c in enumerate(classes)},
            })
        return out

    # --------------------------------------------------------------
    # Persistence
    # --------------------------------------------------------------

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)

    def load(self, path: Path) -> None:
        self.model = joblib.load(path)
        self._trained = True
