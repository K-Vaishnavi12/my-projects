"""ML Playground page.

Live inspector for every ML model shipped in the project.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.components import hero, inject_css, section_title
from app.bootstrap import ensure_bootstrapped
from symposium.config import get_settings
from symposium.ml.agreement_regressor import AgreementRegressor
from symposium.ml.clustering import ArgumentClusterer
from symposium.ml.datasets import debate_outcome_dataset
from symposium.ml.neural_debate_scorer import NeuralDebateScorer, FEATURE_COLS
from symposium.ml.similar_turn_knn import SimilarTurnKNN
from symposium.ml.stance_svm import StanceSVM
from symposium.ml.topic_naive_bayes import TopicNaiveBayes

st.set_page_config(page_title="ML Playground | Symposium", layout="wide")
inject_css()
ensure_bootstrapped()

hero(
    title="ML Playground",
    subtitle="Six machine-learning algorithms. All trained. All poke-able.",
    badges=["SVM", "Naive Bayes", "Regression", "KNN", "K-Means + PCA", "Neural Net"],
)

# ================ Intro cards ================
c1, c2, c3 = st.columns(3)
for col, title, desc, color in [
    (c1, "Trained on synthetic + real data",
     "Datasets are generated deterministically from templates (see `symposium/ml/datasets.py`), plus real turns from your debates once you run some.",
     "#7C3AED"),
    (c2, "Every model has the same shape",
     "train() / predict() / save() / load() \u2014 so you can swap models without touching the app or the debate loop.",
     "#EC4899"),
    (c3, "Metrics are versioned",
     "Full metrics JSON lands in `data/models/metrics.json` after every training run. Reproducible.",
     "#F472B6"),
]:
    with col:
        st.markdown(
            f"""
            <div class="glass" style="padding:1.25rem; min-height:170px;">
                <div style="font-family:'Space Grotesk',sans-serif; font-weight:700;
                            color:{color}; font-size:1.05rem;">{title}</div>
                <div style="margin-top:0.5rem; color:rgba(45,27,78,0.7);
                            font-size:0.9rem; line-height:1.55;">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="glass" style="padding: 1rem 1.25rem; margin-bottom: 1.5rem;">
        <span style="opacity: 0.75;">
            Every model was trained by
            <code>python scripts/train_models.py</code>.
            Full metrics live in <code>data/models/metrics.json</code>.
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

s = get_settings()

tabs = st.tabs([
    "SVM Stance",
    "Naive Bayes Topic",
    "Regression",
    "KNN",
    "K-Means + PCA",
    "Neural Net",
])

# ---------------- SVM ----------------
with tabs[0]:
    section_title("Stance Classifier (Linear SVM)")
    m = StanceSVM()
    p = s.model_dir / "stance_svm.joblib"
    if not p.exists():
        st.warning("Not trained yet - run `.\\tasks.ps1 train` first.")
    else:
        m.load(p)
        text = st.text_area(
            "Enter a candidate agent turn",
            value="I disagree - that overstates the case.",
        )
        if st.button("Classify", key="svm_btn"):
            out = m.predict([text])[0]

            c1, c2 = st.columns([1, 2])
            with c1:
                color = {
                    "agree":    "#34D399",
                    "disagree": "#F87171",
                    "neutral":  "#94A3B8",
                }.get(out["label"], "#FF6B9D")
                st.markdown(
                    f"""
                    <div style="text-align:center; padding: 2rem;
                                background: {color}22; border: 1px solid {color}66;
                                border-radius: 16px;">
                        <div style="font-size: 0.8rem; opacity: 0.7; text-transform: uppercase;">
                            Prediction
                        </div>
                        <div style="font-size: 2rem; font-weight: 700; color: {color};
                                    margin-top: 0.5rem;">
                            {out["label"].title()}
                        </div>
                        <div style="opacity: 0.7; margin-top: 0.25rem;">
                            confidence: {out["score"]:.1%}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c2:
                probs_df = pd.DataFrame(
                    {"stance": list(out["probs"].keys()),
                     "probability": list(out["probs"].values())}
                )
                fig = px.bar(
                    probs_df, x="stance", y="probability",
                    color="stance",
                    color_discrete_map={
                        "agree":    "#34D399",
                        "disagree": "#F87171",
                        "neutral":  "#94A3B8",
                    },
                    template="plotly_white",
                )
                fig.update_layout(
                    showlegend=False,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="#2D1B4E"),
                    height=250,
                )
                st.plotly_chart(fig, use_container_width=True)

# ---------------- Naive Bayes ----------------
with tabs[1]:
    section_title("Topic Classifier (Multinomial Naive Bayes)")
    m = TopicNaiveBayes()
    p = s.model_dir / "topic_naive_bayes.joblib"
    if not p.exists():
        st.warning("Not trained yet.")
    else:
        m.load(p)
        text = st.text_area(
            "Enter any sentence to route to a topic",
            value="Does quantum entanglement violate locality?",
            key="nb_txt",
        )
        if st.button("Route", key="nb_btn"):
            out = m.predict([text])[0]
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown(
                    f"""
                    <div style="text-align:center; padding: 2rem;
                                background: rgba(99,102,241,0.15);
                                border: 1px solid rgba(99,102,241,0.4);
                                border-radius: 16px;">
                        <div style="font-size: 0.8rem; opacity: 0.7; text-transform: uppercase;">
                            Routed topic
                        </div>
                        <div style="font-size: 1.8rem; font-weight: 700; color: #6366F1;
                                    margin-top: 0.5rem;">
                            {out["label"].replace("_", " ").title()}
                        </div>
                        <div style="opacity: 0.7; margin-top: 0.25rem;">
                            confidence: {out["score"]:.1%}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c2:
                probs_df = pd.DataFrame(
                    {"topic": list(out["probs"].keys()),
                     "probability": list(out["probs"].values())}
                ).sort_values("probability", ascending=True)
                fig = px.bar(
                    probs_df, x="probability", y="topic", orientation="h",
                    color="probability", color_continuous_scale="Plasma",
                    template="plotly_white",
                )
                fig.update_layout(
                    showlegend=False,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="#2D1B4E"),
                    coloraxis_showscale=False,
                    height=300,
                )
                st.plotly_chart(fig, use_container_width=True)

# ---------------- Regression ----------------
with tabs[2]:
    section_title("Agreement Regression (Ridge) + Logistic Classifier")
    m = AgreementRegressor()
    p = s.model_dir / "agreement_regressor.joblib"
    if not p.exists():
        st.warning("Not trained yet.")
    else:
        m.load(p)
        text = st.text_area(
            "Enter a candidate turn",
            value="Indeed, the evidence supports that view.",
            key="rg_txt",
        )
        if st.button("Score", key="rg_btn"):
            score = float(m.predict([text])[0])
            color = "#34D399" if score >= 0.6 else ("#F59E0B" if score >= 0.4 else "#F87171")
            st.markdown(
                f"""
                <div style="text-align:center; padding: 2rem;
                            background: {color}22; border: 1px solid {color}66;
                            border-radius: 16px;">
                    <div style="font-size: 0.8rem; opacity: 0.7; text-transform: uppercase;">
                        Agreement score
                    </div>
                    <div style="font-size: 3.5rem; font-weight: 800; color: {color};
                                margin-top: 0.5rem;">
                        {score:.2f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.progress(score)

# ---------------- KNN ----------------
with tabs[3]:
    section_title("Similar-Turn KNN (Over Past Debates)")
    m = SimilarTurnKNN()
    p = s.model_dir / "similar_turn_knn.joblib"
    if not p.exists():
        st.warning("Not fitted yet.")
    else:
        m.load(p)
        text = st.text_area(
            "Find past turns similar to...",
            value="Progress is a double-edged sword.",
            key="knn_txt",
        )
        k = st.slider("K", 1, 10, 5)
        if st.button("Search", key="knn_btn"):
            hits = m.query(text, k=k)
            for h in hits:
                st.markdown(
                    f"""
                    <div style="background: rgba(255,255,255,0.03);
                                border: 1px solid rgba(255,255,255,0.06);
                                border-radius: 12px; padding: 1rem; margin-bottom: 0.75rem;">
                        <div style="display:flex; justify-content:space-between;
                                    font-size:0.85rem; opacity:0.7; margin-bottom:0.5rem;">
                            <span>#{h['rank']}</span>
                            <span style="color:#FF6B9D; font-weight:600;">
                                sim: {h['similarity']:.3f}
                            </span>
                        </div>
                        <div style="line-height:1.5;">{h['text']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ---------------- K-Means + PCA ----------------
with tabs[4]:
    section_title("Argument Clusters (K-Means) & PCA Projection")
    m = ArgumentClusterer()
    p = s.model_dir / "arg_clusterer.joblib"
    if not p.exists():
        st.warning("Not fitted yet.")
    else:
        m.load(p)
        xy, labels = m.project()
        df = pd.DataFrame({"x": xy[:, 0], "y": xy[:, 1], "cluster": labels.astype(str)})
        fig = px.scatter(
            df, x="x", y="y", color="cluster",
            color_discrete_sequence=["#A855F7", "#EC4899", "#F472B6", "#8B5CF6", "#F59E0B"],
            template="plotly_white",
            title=f"K-Means (k={m.k}) on argument embeddings",
        )
        fig.update_traces(marker=dict(size=8, opacity=0.7))
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#2D1B4E"),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Top exemplars per cluster")
        for cid, exemplars in m.top_terms_per_cluster().items():
            with st.expander(f"Cluster {cid}"):
                for ex in exemplars:
                    st.markdown(f"- {ex}")

# ---------------- Neural Net ----------------
with tabs[5]:
    section_title("Neural Debate Scorer (Keras or sklearn MLP)")
    m = NeuralDebateScorer()
    # Prefer .keras (TF) if present, else fallback to .joblib (sklearn MLP)
    p_tf = s.model_dir / "neural_debate_scorer.keras"
    p_sk = s.model_dir / "neural_debate_scorer.joblib"
    p = p_tf if p_tf.exists() else p_sk
    if not p.exists():
        st.warning("Not trained yet.")
    else:
        m.load(p)

        with st.form("nn_form"):
            cols = st.columns(4)
            inputs = {}
            for i, c in enumerate(FEATURE_COLS):
                default = 0.6 if "avg" in c else (6.0 if c == "turns" else 0.3)
                inputs[c] = cols[i % 4].number_input(c, value=float(default))
            submitted = st.form_submit_button(
                "Predict Consensus Tier",
                type="primary",
                use_container_width=True,
            )
        if submitted:
            out = m.predict(inputs)[0]
            color = {"high": "#34D399", "medium": "#F59E0B", "low": "#F87171"}.get(
                out["label"], "#FF6B9D"
            )
            st.markdown(
                f"""
                <div style="text-align:center; padding: 2rem;
                            background: {color}22; border: 1px solid {color}66;
                            border-radius: 16px;">
                    <div style="font-size: 0.8rem; opacity: 0.7; text-transform: uppercase;">
                        Predicted consensus tier
                    </div>
                    <div style="font-size: 2.5rem; font-weight: 800; color: {color};
                                margin-top: 0.5rem;">
                        {out["label"].title()}
                    </div>
                    <div style="opacity: 0.7; margin-top: 0.25rem;">
                        confidence: {out["score"]:.1%}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.caption(
            "Architecture: Sequential MLP with 32 -> 16 -> 3 units, ReLU + softmax, "
            "Adam optimiser, sparse categorical cross-entropy loss."
        )
