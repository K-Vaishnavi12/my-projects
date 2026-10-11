"""Train + save every ML model.

Uses synthetic labeled datasets from :mod:`symposium.ml.datasets`
(they're deterministic + tiny; they let a reviewer reproduce results
in seconds without any external download).

Emits a `data/models/metrics.json` file with every metric for the
report / slides.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# repo root on path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from loguru import logger

from symposium.config import get_settings
from symposium.dwh import Warehouse
from symposium.ml.agreement_regressor import AgreementRegressor
from symposium.ml.clustering import ArgumentClusterer
from symposium.ml.neural_debate_scorer import NeuralDebateScorer
from symposium.ml.similar_turn_knn import SimilarTurnKNN
from symposium.ml.stance_svm import StanceSVM
from symposium.ml.topic_naive_bayes import TopicNaiveBayes
from symposium.ml.datasets import (
    agreement_dataset,
    debate_outcome_dataset,
    stance_dataset,
    topic_dataset,
)


def main() -> None:
    s = get_settings()
    s.model_dir.mkdir(parents=True, exist_ok=True)
    metrics: dict[str, dict] = {}

    # ---- SVM ----
    logger.info("Training stance SVM ...")
    df = stance_dataset()
    svm = StanceSVM()
    metrics["stance_svm"] = svm.train(df["text"].tolist(), df["label"].tolist())
    svm.save(s.model_dir / "stance_svm.joblib")

    # ---- Naive Bayes ----
    logger.info("Training topic Naive Bayes ...")
    df = topic_dataset()
    nb = TopicNaiveBayes()
    metrics["topic_naive_bayes"] = nb.train(df["text"].tolist(), df["label"].tolist())
    nb.save(s.model_dir / "topic_naive_bayes.joblib")

    # ---- Ridge + Logistic ----
    logger.info("Training agreement regressor ...")
    df = agreement_dataset()
    reg = AgreementRegressor()
    metrics["agreement_regressor"] = reg.train(
        df["text"].tolist(), df["target"].tolist()
    )
    reg.save(s.model_dir / "agreement_regressor.joblib")

    # ---- KNN (fitted on existing turns if any, otherwise on stance df) ----
    logger.info("Fitting similar-turn KNN ...")
    knn = SimilarTurnKNN(k=5)
    try:
        wh = Warehouse()
        turns_df = wh.query(
            "SELECT turn_id, persona_key, content AS text FROM fact_turn LIMIT 500"
        )
        wh.close()
        if turns_df.empty:
            raise RuntimeError("no turns yet")
        entries = turns_df.to_dict(orient="records")
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[knn] no debates yet ({exc}); using stance corpus")
        df = stance_dataset()
        entries = [
            {"turn_id": f"synthetic-{i}", "persona_key": "n/a", "text": t}
            for i, t in enumerate(df["text"].tolist())
        ]
    metrics["similar_turn_knn"] = knn.fit(entries)
    knn.save(s.model_dir / "similar_turn_knn.joblib")

    # ---- K-Means + PCA ----
    logger.info("Fitting K-Means + PCA argument clusterer ...")
    ac = ArgumentClusterer(k=5)
    texts = [e["text"] for e in entries]
    metrics["arg_clusterer"] = ac.fit(texts)
    ac.save(s.model_dir / "arg_clusterer.joblib")

    # ---- Neural net ----
    logger.info("Training neural debate scorer ...")
    df = debate_outcome_dataset()
    nn = NeuralDebateScorer()
    metrics["neural_debate_scorer"] = nn.train(df)
    # Detect which backend we're using and pick the right extension
    try:
        import tensorflow  # noqa: F401
        nn.save(s.model_dir / "neural_debate_scorer.keras")
    except ImportError:
        nn.save(s.model_dir / "neural_debate_scorer.joblib")

    # ---- Dump metrics ----
    metrics_path = s.model_dir / "metrics.json"
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, default=str)
    logger.success(f"All metrics -> {metrics_path}")

    print(json.dumps(metrics, indent=2, default=str))


if __name__ == "__main__":
    main()
