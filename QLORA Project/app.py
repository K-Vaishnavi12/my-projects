"""
Phase 4 - Streamlit demo for AmazonQA-RAG.

Run locally
-----------
    streamlit run app.py

Deploy
------
- Streamlit Cloud: point the app entry to `app.py`, add any needed secrets
  (for example `OPENAI_API_KEY`) in the dashboard, and deploy.
- Hugging Face Spaces: create a new Space using the `Streamlit` SDK, push this
  repo, and ensure `requirements.txt` is present at the root.

This app reuses the existing Phase 1 / 2 / 3 modules instead of reimplementing
model loading or retrieval logic:
    - `src.llm_loader` for base / fine-tuned model loading
    - `src.rag_pipeline` for FAISS + retriever + RAG chain
    - `evaluation.ragas_eval` for optional per-query RAGAS scoring

The app is intentionally production-style:
    - cached resources via `st.cache_resource`
    - graceful error messages
    - session-state chat history
    - deploy-friendly environment-variable handling
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st


# Allow `streamlit run app.py` from the project root.
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from configs.config import get_default_config, get_phi2_fallback_config
from evaluation.ragas_eval import evaluate_single_query_with_ragas


logging.basicConfig(
    format="[%(asctime)s] %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger("amazonqa.app")


SYSTEM_LABEL_TO_NAME = {
    "Base LLM": "base",
    "RAG + Base LLM": "rag_base",
    "RAG + Fine-tuned LLM": "rag_finetuned",
}

SYSTEM_NAME_TO_LABEL = {v: k for k, v in SYSTEM_LABEL_TO_NAME.items()}

AMAZON_CSS = """
<style>
    .stApp {
        background: linear-gradient(180deg, #f7f9fb 0%, #eef3f7 100%);
    }
    .main-title {
        color: #111827;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 0.2rem;
    }
    .sub-copy {
        color: #475569;
        margin-bottom: 1rem;
    }
    .answer-card {
        background: #ffffff;
        border: 1px solid #dbe4ee;
        border-left: 6px solid #ff9900;
        border-radius: 14px;
        padding: 1rem 1rem 0.8rem 1rem;
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
        margin-bottom: 1rem;
    }
    .meta-chip {
        display: inline-block;
        padding: 0.25rem 0.55rem;
        border-radius: 999px;
        background: #eaf2ff;
        color: #1d4ed8;
        font-size: 0.82rem;
        margin-right: 0.35rem;
        margin-bottom: 0.35rem;
    }
    .history-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.8rem;
    }
    .small-muted {
        color: #64748b;
        font-size: 0.9rem;
    }
</style>
"""


def _build_cfg(use_phi2: bool):
    cfg = get_phi2_fallback_config() if use_phi2 else get_default_config()
    cfg.paths.ensure_all()
    return cfg


def _get_llm_loader():
    """Lazy import so the app module itself stays importable in thin envs."""
    from src.llm_loader import load_llm

    return load_llm


def _get_rag_pipeline_symbols():
    """Lazy import the Phase 2 building blocks only when needed."""
    from src.rag_pipeline import (
        build_rag_chain,
        build_retriever,
        build_vector_store,
        chunk_documents,
        load_documents,
        load_vector_store,
    )

    return {
        "build_rag_chain": build_rag_chain,
        "build_retriever": build_retriever,
        "build_vector_store": build_vector_store,
        "chunk_documents": chunk_documents,
        "load_documents": load_documents,
        "load_vector_store": load_vector_store,
    }


@st.cache_resource(show_spinner=False)
def get_cfg(use_phi2: bool):
    """Cached config builder so the app reuses directory/path setup."""
    return _build_cfg(use_phi2)


@st.cache_resource(show_spinner=False)
def get_vector_store_cached(use_phi2: bool):
    """Load the FAISS index once per app process."""
    cfg = get_cfg(use_phi2)
    rag = _get_rag_pipeline_symbols()
    try:
        return rag["load_vector_store"](cfg)
    except FileNotFoundError:
        logger.info("FAISS index missing - rebuilding from source corpus")
        docs = rag["load_documents"](cfg)
        chunks = rag["chunk_documents"](docs, cfg)
        return rag["build_vector_store"](chunks, cfg)


@st.cache_resource(show_spinner=False)
def get_retriever_cached(use_phi2: bool, top_k: int):
    """Load the retriever for the current top-k setting."""
    cfg = get_cfg(use_phi2)
    cfg.rag.top_k = top_k
    vector_store = get_vector_store_cached(use_phi2)
    rag = _get_rag_pipeline_symbols()
    return rag["build_retriever"](vector_store, cfg)


@st.cache_resource(show_spinner=False)
def get_llm_cached(
    use_phi2: bool,
    llm_mode: str,
    max_new_tokens: int,
    temperature: float,
):
    """Load the selected model once per unique generation setting."""
    cfg = get_cfg(use_phi2)
    load_llm = _get_llm_loader()
    return load_llm(
        cfg,
        mode=llm_mode,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
    )


@st.cache_resource(show_spinner=False)
def get_rag_chain_cached(
    use_phi2: bool,
    llm_mode: str,
    top_k: int,
    max_new_tokens: int,
    temperature: float,
):
    """Build and cache a RetrievalQA chain for one system configuration."""
    cfg = get_cfg(use_phi2)
    cfg.rag.top_k = top_k
    retriever = get_retriever_cached(use_phi2, top_k)
    llm = get_llm_cached(use_phi2, llm_mode, max_new_tokens, temperature)
    rag = _get_rag_pipeline_symbols()
    return rag["build_rag_chain"](llm, retriever, cfg)


@st.cache_data(show_spinner=False)
def load_phase3_summary() -> Optional[pd.DataFrame]:
    """Load offline RAGAS summary if it exists so the app can display it."""
    cfg = get_default_config()
    summary_path = cfg.paths.results_dir / cfg.eval.summary_filename
    if not summary_path.exists():
        return None
    return pd.read_csv(summary_path, index_col=0)


@st.cache_data(show_spinner=False)
def load_reference_test_set() -> pd.DataFrame:
    """Load the Phase 3 held-out test set for optional per-query ground truth lookup."""
    cfg = get_default_config()
    test_path = cfg.paths.eval_data_dir / cfg.eval.test_set_filename
    if not test_path.exists():
        return pd.DataFrame(columns=["question", "ground_truth_answer"])
    return pd.read_csv(test_path)


def _get_ground_truth_from_test_set(question: str) -> Optional[str]:
    """Return the reference answer if the question exactly matches the Phase 3 test set."""
    df = load_reference_test_set()
    if df.empty or "question" not in df or "ground_truth_answer" not in df:
        return None
    match = df[df["question"].astype(str).str.strip() == question.strip()]
    if match.empty:
        return None
    return str(match.iloc[0]["ground_truth_answer"]).strip()


def _extract_similarity_score(doc: Any) -> Optional[float]:
    """Best-effort extraction of a score from LangChain doc metadata."""
    metadata = getattr(doc, "metadata", {}) or {}
    for key in ("score", "similarity", "distance", "relevance_score"):
        value = metadata.get(key)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
    return None


def answer_question(
    system_name: str,
    question: str,
    *,
    use_phi2: bool,
    top_k: int,
    max_new_tokens: int,
    temperature: float,
) -> Dict[str, Any]:
    """
    Unified app-facing inference API.

    Args:
        system_name: 'base', 'rag_base', or 'rag_finetuned'.
        question: End-user query.

    Returns:
        {
          'answer': str,
          'contexts': List[str],
          'meta': {
              'latency_seconds': float,
              'system_name': str,
              'retrieved_docs': int,
              'scores': List[Optional[float]],
          }
        }
    """
    cfg = get_cfg(use_phi2)
    cfg.rag.top_k = top_k

    started = time.perf_counter()

    if system_name == "base":
        llm = get_llm_cached(use_phi2, "base", max_new_tokens, temperature)
        prompt = cfg.prompt_template.format(question=question, answer="").rstrip("</s>").rstrip()
        answer = llm.invoke(prompt)
        contexts: List[str] = []
        scores: List[Optional[float]] = []
    else:
        llm_mode = "base" if system_name == "rag_base" else "finetuned"
        chain = get_rag_chain_cached(
            use_phi2,
            llm_mode,
            top_k,
            max_new_tokens,
            temperature,
        )
        result = chain.invoke({"query": question})
        answer = (result.get("result") or result.get("answer") or "").strip()
        source_documents = result.get("source_documents") or []
        contexts = [doc.page_content for doc in source_documents]
        scores = [_extract_similarity_score(doc) for doc in source_documents]

    latency = time.perf_counter() - started
    return {
        "answer": answer.strip() if isinstance(answer, str) else str(answer),
        "contexts": contexts,
        "meta": {
            "latency_seconds": latency,
            "system_name": system_name,
            "retrieved_docs": len(contexts),
            "scores": scores,
        },
    }


def maybe_compute_query_ragas(
    *,
    question: str,
    answer: str,
    contexts: List[str],
    enabled: bool,
    ground_truth_answer: Optional[str],
    use_phi2: bool,
) -> Dict[str, Any]:
    """Compute lightweight per-query RAGAS if the user explicitly opts in."""
    if not enabled:
        return {"enabled": False, "skipped": True, "message": ""}

    cfg = get_cfg(use_phi2)
    result = evaluate_single_query_with_ragas(
        question=question,
        generated_answer=answer,
        contexts=contexts,
        ground_truth_answer=ground_truth_answer,
        cfg=cfg,
    )
    result["enabled"] = True
    return result


def render_answer_card(result: Dict[str, Any], label: str) -> None:
    """Render the primary answer block."""
    meta = result["meta"]
    chips = [
        f'<span class="meta-chip">System: {label}</span>',
        f'<span class="meta-chip">Latency: {meta["latency_seconds"]:.2f}s</span>',
        f'<span class="meta-chip">Contexts: {meta["retrieved_docs"]}</span>',
    ]
    st.markdown(
        "<div class='answer-card'>"
        + "".join(chips)
        + f"<p style='margin-top:0.8rem; color:#0f172a; line-height:1.6;'>{result['answer']}</p>"
        + "</div>",
        unsafe_allow_html=True,
    )


def render_contexts(contexts: List[str], scores: List[Optional[float]]) -> None:
    """Expandable retrieved context list for RAG systems."""
    if not contexts:
        st.info("No retrieval context for the Base LLM mode.")
        return

    with st.expander("Retrieved Context Chunks", expanded=False):
        for idx, context in enumerate(contexts, start=1):
            score = scores[idx - 1] if idx - 1 < len(scores) else None
            label = f"Chunk {idx}"
            if score is not None:
                label += f"  |  score: {score:.4f}"
            st.markdown(f"**{label}**")
            st.caption(context)
            if idx != len(contexts):
                st.divider()


def render_ragas_panel(ragas_result: Dict[str, Any]) -> None:
    """Display on-demand per-query RAGAS, or a clear skip message."""
    st.subheader("Per-query RAGAS")
    if not ragas_result.get("enabled"):
        st.caption("Per-query RAGAS is disabled. Offline evaluation lives in `results/ragas_summary.csv`.")
        return

    if ragas_result.get("skipped"):
        st.info(ragas_result.get("message") or "RAGAS was skipped for this query.")
        return

    scores = ragas_result.get("scores", {})
    cols = st.columns(2)
    with cols[0]:
        faithfulness = scores.get("faithfulness")
        st.metric("Faithfulness", f"{faithfulness:.3f}" if faithfulness is not None else "n/a")
    with cols[1]:
        relevancy = scores.get("answer_relevancy")
        st.metric("Answer Relevancy", f"{relevancy:.3f}" if relevancy is not None else "n/a")
    st.caption("Online scoring uses only faithfulness + answer_relevancy to keep the live app reasonably responsive.")


def init_session_state() -> None:
    """Ensure chat history exists."""
    if "history" not in st.session_state:
        st.session_state.history = []


def push_history(question: str, answer: str, system_name: str) -> None:
    """Append one interaction to the persistent chat-like history."""
    st.session_state.history.insert(
        0,
        {
            "question": question,
            "answer": answer,
            "system_name": system_name,
            "timestamp": time.strftime("%H:%M:%S"),
        },
    )


def render_history() -> None:
    """Show prior question/answer pairs."""
    if not st.session_state.history:
        st.caption("No chat history yet. Ask a question to start the demo.")
        return

    st.subheader("Chat History")
    for item in st.session_state.history:
        label = SYSTEM_NAME_TO_LABEL.get(item["system_name"], item["system_name"])
        st.markdown(
            "<div class='history-card'>"
            f"<div class='small-muted'>{item['timestamp']}  |  {label}</div>"
            f"<p><strong>Q:</strong> {item['question']}</p>"
            f"<p style='margin-bottom:0;'><strong>A:</strong> {item['answer']}</p>"
            "</div>",
            unsafe_allow_html=True,
        )


def main() -> None:
    st.set_page_config(
        page_title="AmazonQA-RAG Demo",
        page_icon="🛒",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(AMAZON_CSS, unsafe_allow_html=True)
    init_session_state()

    st.sidebar.title("AmazonQA-RAG")
    st.sidebar.markdown(
        "Ask Amazon-style product questions against three systems: base LLM, "
        "RAG + base LLM, and RAG + fine-tuned LLM."
    )

    system_label = st.sidebar.radio(
        "Choose system",
        options=list(SYSTEM_LABEL_TO_NAME.keys()),
        index=2,
    )
    system_name = SYSTEM_LABEL_TO_NAME[system_label]

    use_phi2 = st.sidebar.toggle(
        "Use Phi-2 fallback artifacts",
        value=False,
        help="Enable this only if you fine-tuned / indexed with the Phi-2 fallback configuration.",
    )
    top_k = st.sidebar.slider("Top-K retrieval", min_value=1, max_value=10, value=5)
    max_new_tokens = st.sidebar.slider("Max answer length", min_value=64, max_value=512, value=256, step=32)
    temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, value=0.3, step=0.05)
    enable_query_ragas = st.sidebar.toggle(
        "Compute RAGAS metrics for this query (slower)",
        value=False,
        help="Computes faithfulness + answer relevancy on demand. Best for demo queries, not bulk use.",
    )
    manual_ground_truth = st.sidebar.text_area(
        "Optional reference answer for per-query RAGAS",
        value="",
        help="If blank, the app tries to find a matching question in data/eval/test_qa.csv. Otherwise per-query RAGAS is skipped.",
    )

    summary_df = load_phase3_summary()
    if summary_df is not None:
        st.sidebar.markdown("### Offline Phase 3 Summary")
        st.sidebar.dataframe(summary_df.round(3), use_container_width=True)
    else:
        st.sidebar.caption("Offline RAGAS summary not found yet. Run `python -m evaluation.ragas_eval --system all --n_samples 100` to populate it.")

    st.markdown("<h1 class='main-title'>AmazonQA-RAG Demo</h1>", unsafe_allow_html=True)
    st.markdown(
        "<div class='sub-copy'>"
        "Compare raw generation against retrieval-augmented generation, and inspect the supporting context chunks behind each answer."
        "</div>",
        unsafe_allow_html=True,
    )

    question = st.text_area(
        "Ask a product question",
        value="Does the Echo Dot 5th gen work with Apple Music and can I pair multiple devices?",
        height=100,
        placeholder="Type an Amazon-style customer question...",
    )

    action_cols = st.columns([1, 1, 5])
    ask_clicked = action_cols[0].button("Ask", type="primary", use_container_width=True)
    clear_clicked = action_cols[1].button("Clear History", use_container_width=True)
    if clear_clicked:
        st.session_state.history = []
        st.rerun()

    if ask_clicked:
        cleaned_question = question.strip()
        if not cleaned_question:
            st.error("Please enter a question before clicking Ask.")
            st.stop()

        try:
            with st.status("Loading models...", expanded=True) as status:
                status.write("Preparing cached model and retriever resources...")
                if system_name == "base":
                    get_llm_cached(use_phi2, "base", max_new_tokens, temperature)
                else:
                    llm_mode = "base" if system_name == "rag_base" else "finetuned"
                    status.write("Retrieving context...")
                    get_rag_chain_cached(use_phi2, llm_mode, top_k, max_new_tokens, temperature)

                status.write("Generating answer...")
                result = answer_question(
                    system_name,
                    cleaned_question,
                    use_phi2=use_phi2,
                    top_k=top_k,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                )
                status.update(label="Answer ready", state="complete")

            st.subheader("Answer")
            render_answer_card(result, system_label)
            render_contexts(result["contexts"], result["meta"].get("scores", []))

            ground_truth_answer = manual_ground_truth.strip() or _get_ground_truth_from_test_set(cleaned_question)
            ragas_result: Dict[str, Any]
            if enable_query_ragas:
                with st.spinner("Computing per-query RAGAS (faithfulness + answer relevancy)..."):
                    ragas_result = maybe_compute_query_ragas(
                        question=cleaned_question,
                        answer=result["answer"],
                        contexts=result["contexts"],
                        enabled=True,
                        ground_truth_answer=ground_truth_answer,
                        use_phi2=use_phi2,
                    )
            else:
                ragas_result = {"enabled": False, "skipped": True, "message": ""}

            render_ragas_panel(ragas_result)
            push_history(cleaned_question, result["answer"], system_name)

        except FileNotFoundError as exc:
            st.error(
                "Required model artifact is missing. "
                "Run Phase 1 / Phase 2 first so the LoRA adapter and FAISS index exist.\n\n"
                f"Details: {exc}"
            )
        except Exception as exc:
            logger.exception("App query failed")
            st.error(
                "The app hit an unexpected error while answering your question.\n\n"
                f"Details: {exc}"
            )

    st.divider()
    render_history()

    with st.expander("Deployment Notes", expanded=False):
        st.markdown(
            "- Local: `streamlit run app.py`\n"
            "- Streamlit Cloud: set `app.py` as the entrypoint and add any secrets in the dashboard.\n"
            "- Hugging Face Spaces: create a Streamlit Space, push this repo, and keep `requirements.txt` at the root.\n"
            "- Any external API key (for example `OPENAI_API_KEY` for per-query RAGAS) must come from environment variables or platform secrets, never hard-coded."
        )


if __name__ == "__main__":
    main()
