"""
RAGAS evaluation engine for Phase 3.

Public API
----------
    evaluate_system_with_ragas(system_name, qa_df, n_samples=100)
        Generate answers + contexts for one of the three systems and score
        them against `EvalConfig.metrics`. Returns per-sample + aggregate.

    run_full_evaluation(cfg, n_samples=None, smoke_test=False)
        Orchestrates all three systems end-to-end, writes per-system score
        CSVs + a summary CSV + comparison plots.

CLI
---
    python -m evaluation.ragas_eval --system all --n_samples 100
    python -m evaluation.ragas_eval --system rag_finetuned --n_samples 50
    python -m evaluation.ragas_eval --smoke-test          # 5 rows, all systems

Adding new metrics
------------------
1. Pip-install the metric class (RAGAS ships dozens — see ragas/metrics/).
2. Append its name to `cfg.eval.metrics`.
3. Register the import in `_get_ragas_metrics()` below.

Judge backend
-------------
RAGAS's faithfulness + answer_relevancy require an LLM-as-judge. Three options:
    - 'openai'  : set OPENAI_API_KEY env var, uses cfg.eval.ragas_openai_model
    - 'local'   : uses cfg.eval.ragas_local_judge_model via HF pipeline
    - 'auto'    : openai if OPENAI_API_KEY present, else local
The chosen backend is logged at run start.
"""

from __future__ import annotations

import gc
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Allow `python -m evaluation.ragas_eval`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from configs.config import FineTuneConfig, get_default_config
from evaluation.generators import GeneratorRegistry, SYSTEM_NAMES
from evaluation.test_set import load_test_set

logger = logging.getLogger("amazonqa.eval.ragas")


# ===========================================================================
# 1. RAGAS judge / metric setup
# ===========================================================================
def _resolve_judge_backend(cfg: FineTuneConfig) -> str:
    """Resolve 'auto' to either 'openai' or 'local' based on env."""
    backend = cfg.eval.ragas_judge_backend
    if backend == "auto":
        backend = "openai" if os.environ.get("OPENAI_API_KEY") else "local"
    if backend not in ("openai", "local"):
        raise ValueError(
            f"Invalid ragas_judge_backend '{backend}'. "
            "Choose one of: 'openai', 'local', 'auto'."
        )
    return backend


def _build_ragas_judge(cfg: FineTuneConfig) -> Tuple[Any, Any]:
    """
    Construct the (llm, embeddings) pair RAGAS will use to score samples.

    Returns wrapped LangChain objects RAGAS understands. We try the modern
    `ragas.llms.LangchainLLMWrapper` API, then fall back gracefully.
    """
    backend = _resolve_judge_backend(cfg)
    logger.info("RAGAS judge backend: %s", backend)

    # ---------------- Embeddings (same for both backends) ----------------
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:  # pragma: no cover
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings  # type: ignore
        except ImportError:
            from langchain.embeddings import HuggingFaceEmbeddings  # type: ignore

    embeddings = HuggingFaceEmbeddings(
        model_name=cfg.eval.ragas_embedding_model,
        encode_kwargs={"normalize_embeddings": True},
    )

    # ---------------- LLM ----------------
    if backend == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:  # pragma: no cover
            from langchain_community.chat_models import ChatOpenAI  # type: ignore
        judge_llm = ChatOpenAI(
            model=cfg.eval.ragas_openai_model,
            temperature=0,
        )
    else:
        # Local HF pipeline judge — small, CPU-friendly seq2seq for cost reasons
        from transformers import pipeline as hf_pipeline

        try:
            from langchain_huggingface import HuggingFacePipeline
        except ImportError:  # pragma: no cover
            try:
                from langchain_community.llms import HuggingFacePipeline  # type: ignore
            except ImportError:
                from langchain.llms import HuggingFacePipeline  # type: ignore

        local_pipe = hf_pipeline(
            task="text2text-generation",
            model=cfg.eval.ragas_local_judge_model,
            max_new_tokens=256,
        )
        judge_llm = HuggingFacePipeline(pipeline=local_pipe)

    # ---------------- Wrap for RAGAS ----------------
    try:
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings import LangchainEmbeddingsWrapper

        wrapped_llm = LangchainLLMWrapper(judge_llm)
        wrapped_emb = LangchainEmbeddingsWrapper(embeddings)
        return wrapped_llm, wrapped_emb
    except ImportError:  # pragma: no cover
        # Older RAGAS API accepted raw LangChain objects directly.
        return judge_llm, embeddings


def _get_ragas_metrics(metric_names: List[str]) -> List[Any]:
    """Map metric-name strings to RAGAS metric instances."""
    try:
        from ragas import metrics as rm
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "ragas is required for Phase 3 evaluation. "
            "Install with `pip install ragas==0.1.21`."
        ) from exc

    name_to_metric = {
        "faithfulness": rm.faithfulness,
        "answer_relevancy": rm.answer_relevancy,
        "context_precision": rm.context_precision,
        "context_recall": rm.context_recall,
        # Easy to extend:
        # "answer_similarity":  rm.answer_similarity,
        # "answer_correctness": rm.answer_correctness,
    }
    out = []
    for name in metric_names:
        if name not in name_to_metric:
            raise ValueError(
                f"Unsupported metric '{name}'. "
                f"Known: {sorted(name_to_metric.keys())}"
            )
        out.append(name_to_metric[name])
    return out


def _get_ragas_evaluate_fn():
    """Import seam so tests can monkeypatch RAGAS evaluation cheaply."""
    try:
        from ragas import evaluate as ragas_evaluate
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "ragas is required for evaluation. "
            "Install with `pip install ragas==0.1.21`."
        ) from exc
    return ragas_evaluate


# ===========================================================================
# 2. Per-system evaluation
# ===========================================================================
def evaluate_system_with_ragas(
    system_name: str,
    qa_df: pd.DataFrame,
    n_samples: int = 100,
    *,
    cfg: Optional[FineTuneConfig] = None,
    registry: Optional[GeneratorRegistry] = None,
    save_per_sample: bool = True,
) -> pd.DataFrame:
    """
    Evaluate ONE system with RAGAS and return per-sample + aggregate scores.

    Args:
        system_name: One of {"base", "rag_base", "rag_finetuned"}.
        qa_df: DataFrame with at minimum columns
               ['question', 'ground_truth_answer'].
        n_samples: Cap on the number of rows scored (head of the DataFrame).
        cfg: Project config (defaults to `get_default_config()`).
        registry: Optional shared `GeneratorRegistry` so multi-system runs
                  reuse the FAISS retriever.
        save_per_sample: If True, write
                  `results/{system_name}_ragas_scores.csv`.

    Returns:
        A DataFrame with one row per sample plus an extra `MEAN` row at the
        end. Columns:
            question, ground_truth_answer, generated_answer, contexts,
            <metric_1>, <metric_2>, ...
    """
    if system_name not in SYSTEM_NAMES:
        raise ValueError(
            f"Unknown system '{system_name}'. Must be one of {SYSTEM_NAMES}."
        )

    cfg = cfg or get_default_config()
    registry = registry or GeneratorRegistry(cfg)

    df = qa_df.head(n_samples).reset_index(drop=True)
    logger.info(
        "Evaluating system='%s' on %d samples (metrics=%s)",
        system_name,
        len(df),
        cfg.eval.metrics,
    )

    # ----------------------------------------------------------------------
    # Phase A: generate answers + contexts for every question
    # ----------------------------------------------------------------------
    generated_rows: List[Dict[str, Any]] = []
    for i, row in df.iterrows():
        if (i + 1) % 10 == 0 or i == 0:
            logger.info("  generating %d/%d", i + 1, len(df))
        out = registry.generate(system_name, row["question"])

        # RAGAS requires a non-empty contexts list — even for the bare base
        # LLM. Use a single sentinel chunk so context_precision/recall fall
        # back to "no useful context" as expected.
        contexts = out["contexts"] if out["contexts"] else ["[no_context_available]"]

        generated_rows.append(
            {
                "question": row["question"],
                "ground_truth": row["ground_truth_answer"],
                "answer": out["answer"],
                "contexts": contexts,
            }
        )

    # ----------------------------------------------------------------------
    # Phase B: hand the data to RAGAS
    # ----------------------------------------------------------------------
    try:
        from datasets import Dataset
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "ragas + datasets are required. "
            "Install with `pip install ragas==0.1.21 datasets==2.21.0`."
        ) from exc

    ragas_ds = Dataset.from_list(generated_rows)
    ragas_evaluate = _get_ragas_evaluate_fn()
    judge_llm, judge_emb = _build_ragas_judge(cfg)
    metrics = _get_ragas_metrics(cfg.eval.metrics)

    logger.info("Running RAGAS scoring (this can take 5-15 min)...")
    # The RAGAS API accepts llm + embeddings since 0.1.x; older versions
    # auto-detect from env. We pass both for forward compatibility.
    try:
        result = ragas_evaluate(
            dataset=ragas_ds,
            metrics=metrics,
            llm=judge_llm,
            embeddings=judge_emb,
            raise_exceptions=False,
        )
    except TypeError:  # pragma: no cover — older ragas
        result = ragas_evaluate(dataset=ragas_ds, metrics=metrics)

    # ----------------------------------------------------------------------
    # Phase C: assemble the per-sample DataFrame
    # ----------------------------------------------------------------------
    # `result` exposes a `.to_pandas()` method on every recent RAGAS release.
    try:
        scored = result.to_pandas()
    except AttributeError:  # pragma: no cover — very old API
        scored = pd.DataFrame(result.scores)

    # Standardise column names to match the spec (`generated_answer`)
    scored = scored.rename(
        columns={
            "answer": "generated_answer",
            "ground_truth": "ground_truth_answer",
        }
    )

    # Append a MEAN summary row at the bottom (handy for quick eyeballing)
    metric_cols = [c for c in cfg.eval.metrics if c in scored.columns]
    means = {c: scored[c].mean() for c in metric_cols}
    means_row = {col: ("MEAN" if col == "question" else "") for col in scored.columns}
    means_row.update(means)
    scored = pd.concat([scored, pd.DataFrame([means_row])], ignore_index=True)

    # ----------------------------------------------------------------------
    # Phase D: persist
    # ----------------------------------------------------------------------
    if save_per_sample:
        out_path = cfg.paths.results_dir / cfg.eval.per_system_filename_template.format(
            system=system_name
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        scored.to_csv(out_path, index=False)
        logger.info("Per-sample scores saved to %s", out_path)

    # Friendly log line summarising the means
    logger.info(
        "[%s] %s",
        system_name,
        "  ".join(f"{m}={means.get(m, float('nan')):.3f}" for m in metric_cols),
    )
    return scored


# ===========================================================================
# 3. Single-query helper (used by the Streamlit demo)
# ===========================================================================
def evaluate_single_query_with_ragas(
    *,
    question: str,
    generated_answer: str,
    contexts: List[str],
    ground_truth_answer: Optional[str] = None,
    cfg: Optional[FineTuneConfig] = None,
) -> Dict[str, Any]:
    """
    Score one query interactively inside the Streamlit app.

    We intentionally keep this lightweight: only `faithfulness` and
    `answer_relevancy` are computed, because those are the two most useful
    online diagnostics and avoid the retrieval-heavy cost of the full offline
    Phase 3 benchmark.

    If `ground_truth_answer` is missing or blank, we skip scoring and return a
    friendly message. This avoids presenting misleading partial metrics in the
    live demo when the user asks an arbitrary question with no reference answer.
    """
    cfg = cfg or get_default_config()

    if not ground_truth_answer or not ground_truth_answer.strip():
        return {
            "skipped": True,
            "message": (
                "Per-query RAGAS skipped because no reference answer was "
                "provided. Add a ground-truth answer in the sidebar to enable it."
            ),
            "scores": {},
        }

    try:
        from datasets import Dataset
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "ragas + datasets are required for per-query scoring. "
            "Install with `pip install ragas==0.1.21 datasets==2.21.0`."
        ) from exc

    row = {
        "question": question,
        "ground_truth": ground_truth_answer,
        "answer": generated_answer,
        "contexts": contexts or ["[no_context_available]"],
    }
    ragas_ds = Dataset.from_list([row])
    ragas_evaluate = _get_ragas_evaluate_fn()
    judge_llm, judge_emb = _build_ragas_judge(cfg)
    metrics = _get_ragas_metrics(["faithfulness", "answer_relevancy"])

    try:
        result = ragas_evaluate(
            dataset=ragas_ds,
            metrics=metrics,
            llm=judge_llm,
            embeddings=judge_emb,
            raise_exceptions=False,
        )
    except TypeError:  # pragma: no cover
        result = ragas_evaluate(dataset=ragas_ds, metrics=metrics)

    try:
        scored = result.to_pandas()
    except AttributeError:  # pragma: no cover
        scored = pd.DataFrame(result.scores)

    if scored.empty:
        return {
            "skipped": True,
            "message": "RAGAS returned no scores for this query.",
            "scores": {},
        }

    scores = {
        "faithfulness": scored.iloc[0].get("faithfulness"),
        "answer_relevancy": scored.iloc[0].get("answer_relevancy"),
    }
    return {
        "skipped": False,
        "message": "",
        "scores": scores,
    }


# ===========================================================================
# 3. Three-system orchestrator
# ===========================================================================
def run_full_evaluation(
    cfg: Optional[FineTuneConfig] = None,
    *,
    n_samples: Optional[int] = None,
    systems: Optional[List[str]] = None,
    smoke_test: bool = False,
    save_plots: bool = True,
) -> pd.DataFrame:
    """
    Run RAGAS over every requested system and produce the comparison summary.

    Args:
        cfg: Project config.
        n_samples: Override `cfg.eval.test_set_size`.
        systems: Subset of {'base', 'rag_base', 'rag_finetuned'};
                 defaults to all three.
        smoke_test: Use `cfg.eval.smoke_test_size` (default 5) — handy for
                    verifying the wiring without spending GPU budget.
        save_plots: Generate the bar chart + radar chart.

    Returns:
        Summary DataFrame indexed by system name with one column per metric
        (e.g. `faithfulness_mean`).
    """
    cfg = cfg or get_default_config()
    cfg.paths.ensure_all()
    systems = systems or list(SYSTEM_NAMES)
    n_samples = (
        cfg.eval.smoke_test_size
        if smoke_test
        else (n_samples or cfg.eval.test_set_size)
    )

    logger.info(
        "=== Phase 3 RAGAS run | systems=%s | n_samples=%d | smoke_test=%s ===",
        systems,
        n_samples,
        smoke_test,
    )

    # 1. Test set
    qa_df = load_test_set(cfg, n_samples=n_samples)
    if len(qa_df) < n_samples:
        logger.warning(
            "Test set has only %d rows but %d requested — capping at %d.",
            len(qa_df),
            n_samples,
            len(qa_df),
        )
        n_samples = len(qa_df)

    # 2. Iterate
    registry = GeneratorRegistry(cfg)
    summary_rows = []
    for system_name in systems:
        logger.info("--- System: %s ---", system_name)
        scored = evaluate_system_with_ragas(
            system_name=system_name,
            qa_df=qa_df,
            n_samples=n_samples,
            cfg=cfg,
            registry=registry,
            save_per_sample=True,
        )
        # Pull means from the trailing MEAN row
        mean_row = scored.iloc[-1]
        summary_rows.append(
            {
                "system": system_name,
                **{
                    f"{m}_mean": mean_row[m]
                    for m in cfg.eval.metrics
                    if m in scored.columns
                },
            }
        )
        # Free GPU between systems (the registry handles eviction internally
        # but we also drop our local refs explicitly).
        del scored
        gc.collect()
        registry.unload(system_name)

    summary = pd.DataFrame(summary_rows).set_index("system")

    # 3. Persist summary
    summary_path = cfg.paths.results_dir / cfg.eval.summary_filename
    summary.to_csv(summary_path)
    logger.info("Summary CSV written to %s", summary_path)
    logger.info("\n%s", summary.round(3).to_string())

    # 4. Plots
    if save_plots:
        try:
            from evaluation.visualize import (
                plot_ragas_comparison,
                plot_ragas_radar,
            )

            plot_ragas_comparison(summary, cfg=cfg)
            plot_ragas_radar(summary, cfg=cfg)
        except Exception as exc:  # pragma: no cover
            logger.warning("Plot generation failed: %s", exc)

    return summary


# ===========================================================================
# 4. CLI
# ===========================================================================
def _build_argparser():
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m evaluation.ragas_eval",
        description=(
            "Phase 3 RAGAS evaluation for AmazonQA-RAG. "
            "Compares Base / RAG+Base / RAG+Fine-tuned on a held-out Amazon QA split."
        ),
    )
    parser.add_argument(
        "--system",
        type=str,
        default="all",
        choices=("all", "base", "rag_base", "rag_finetuned"),
        help="Which system(s) to evaluate. 'all' runs the three-way comparison.",
    )
    parser.add_argument(
        "--n_samples",
        type=int,
        default=None,
        help="Override test-set size (default: cfg.eval.test_set_size = 100).",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run on cfg.eval.smoke_test_size (default 5) rows for a quick wiring check.",
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip generating bar + radar charts.",
    )
    parser.add_argument(
        "--rebuild-test-set",
        action="store_true",
        help="Force regeneration of data/test_qa.csv before evaluating.",
    )
    return parser


def _cli_main(argv: Optional[List[str]] = None) -> int:
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        level=logging.INFO,
    )
    args = _build_argparser().parse_args(argv)
    cfg = get_default_config()

    # Optional rebuild
    if args.rebuild_test_set:
        from evaluation.test_set import build_test_set

        build_test_set(cfg, n_samples=args.n_samples, overwrite=True)

    systems = list(SYSTEM_NAMES) if args.system == "all" else [args.system]
    run_full_evaluation(
        cfg,
        n_samples=args.n_samples,
        systems=systems,
        smoke_test=args.smoke_test,
        save_plots=not args.no_plots,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli_main())


__all__ = [
    "evaluate_single_query_with_ragas",
    "evaluate_system_with_ragas",
    "run_full_evaluation",
]
