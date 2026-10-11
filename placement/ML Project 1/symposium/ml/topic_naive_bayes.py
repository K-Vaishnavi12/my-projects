"""Topic classifier - Multinomial Naive Bayes.

Classifies free text into one of the 5 topic buckets used by
the ETL (history / science / philosophy / literature / current_events).

Used by the moderator agent to route ambiguous questions to the
right sub-corpus.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
from loguru import logger
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


class TopicNaiveBayes:
    def __init__(self) -> None:
        self.model = Pipeline(
            steps=[
                (
                    "tfidf",
                    TfidfVectorizer(
                        ngram_range=(1, 2),
                        max_features=15_000,
                        min_df=2,
                        stop_words="english",
                        sublinear_tf=True,
                    ),
                ),
                ("clf", MultinomialNB(alpha=0.3)),
            ]
        )
        self._trained = False

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
            "classes": sorted(set(y)),
            "n_train": len(X_tr),
            "n_test": len(X_te),
        }
        self._trained = True
        logger.info(f"[topic_nb] trained. metrics={metrics}")
        return metrics

    def predict(self, texts: list[str]) -> list[dict[str, Any]]:
        if not self._trained:
            raise RuntimeError("Model not trained.")
        probs = self.model.predict_proba(texts)
        classes = self.model.named_steps["clf"].classes_
        return [
            {
                "text": t,
                "label": classes[int(np.argmax(probs[i]))],
                "score": float(np.max(probs[i])),
                "probs": {c: float(probs[i, j]) for j, c in enumerate(classes)},
            }
            for i, t in enumerate(texts)
        ]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)

    def load(self, path: Path) -> None:
        self.model = joblib.load(path)
        self._trained = True
