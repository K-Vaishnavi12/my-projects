"""First-run bootstrap for cloud deployments.

Streamlit Cloud starts with an empty `data/` folder. On first launch we:
1. Ensure directory structure exists
2. Train ML models if missing (fast, ~30s)
3. Load a small Wikipedia corpus into Mongo if missing

Called from every Streamlit page via ``ensure_bootstrapped()``. The
work is guarded by a session-state flag so it only runs once per
container start.
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from loguru import logger

from symposium.config import get_settings


BOOTSTRAP_KEY = "_symposium_bootstrapped_v1"


def _train_if_missing() -> None:
    """Train + save ML models if the joblib files don't exist yet."""
    s = get_settings()
    marker = s.model_dir / "stance_svm.joblib"
    if marker.exists():
        return

    logger.info("[bootstrap] Training ML models (first-run only)...")
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

    df = stance_dataset()
    m = StanceSVM(); m.train(df["text"].tolist(), df["label"].tolist())
    m.save(s.model_dir / "stance_svm.joblib")

    df = topic_dataset()
    m = TopicNaiveBayes(); m.train(df["text"].tolist(), df["label"].tolist())
    m.save(s.model_dir / "topic_naive_bayes.joblib")

    df = agreement_dataset()
    m = AgreementRegressor(); m.train(df["text"].tolist(), df["target"].tolist())
    m.save(s.model_dir / "agreement_regressor.joblib")

    # KNN + K-Means (on the same synthetic stance data)
    df = stance_dataset()
    entries = [
        {"turn_id": f"seed-{i}", "persona_key": "n/a", "text": t}
        for i, t in enumerate(df["text"].tolist())
    ]
    knn = SimilarTurnKNN(k=5); knn.fit(entries)
    knn.save(s.model_dir / "similar_turn_knn.joblib")

    texts = [e["text"] for e in entries]
    ac = ArgumentClusterer(k=5); ac.fit(texts)
    ac.save(s.model_dir / "arg_clusterer.joblib")

    df = debate_outcome_dataset()
    nn = NeuralDebateScorer(); nn.train(df)
    try:
        import tensorflow  # noqa: F401
        nn.save(s.model_dir / "neural_debate_scorer.keras")
    except ImportError:
        nn.save(s.model_dir / "neural_debate_scorer.joblib")

    logger.success("[bootstrap] ML models trained.")


def _load_corpus_if_empty() -> None:
    """Load a tiny Wikipedia corpus if Mongo is empty. Non-fatal on error."""
    try:
        from symposium.etl.pipeline import run_pipeline
        from symposium.dwh import Warehouse

        wh = Warehouse()
        docs = wh.counts().get("dim_document", 0)
        wh.close()
        if docs > 0:
            return

        logger.info("[bootstrap] Loading initial corpus (first-run only)...")
        # small footprint for first boot; user can re-run ETL for the full set
        run_pipeline(topics=["current_events", "philosophy"])
        logger.success("[bootstrap] Initial corpus loaded.")
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[bootstrap] Skipping corpus load (probably missing MONGODB_URI): {exc}")


def ensure_bootstrapped() -> None:
    """Idempotent: run once per container start."""
    if st.session_state.get(BOOTSTRAP_KEY):
        return

    s = get_settings()
    s.ensure_dirs()

    with st.spinner("First-run setup: training models + loading corpus (30-90s)..."):
        try:
            _train_if_missing()
        except Exception as exc:  # noqa: BLE001
            logger.error(f"[bootstrap] Model training failed: {exc}")

        # Only try Mongo bootstrap if URI is a real Atlas URL
        if s.mongodb_uri and "mongodb+srv" in s.mongodb_uri:
            _load_corpus_if_empty()

    st.session_state[BOOTSTRAP_KEY] = True
