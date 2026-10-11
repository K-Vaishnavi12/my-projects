"""
Held-out test set builder for Phase 3 (RAGAS evaluation).

Carves a non-overlapping slice from the same `embedding-data/Amazon-QA`
dataset used in Phase 1 — but with a *different* seed (`EvalConfig.test_set_seed`)
so the test rows are statistically isolated from the rows the model saw during
QLoRA fine-tuning.

Public API
----------
    build_test_set(cfg, n_samples=None, overwrite=False) -> pd.DataFrame
        Materialise the test set as `data/test_qa.csv`.

    load_test_set(cfg, n_samples=None) -> pd.DataFrame
        Load (or rebuild on first call) the cached test set.

DataFrame schema
----------------
    question                 : str   — user question fed into all 3 systems
    ground_truth_answer      : str   — gold answer from the dataset
    context_docs             : str   — retrieval context placeholder (filled
                                       at generate-time by the RAG pipeline);
                                       always empty in the saved CSV.
    source_index             : int   — original index into the HF dataset
                                       (handy for debugging / re-sampling).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

# Allow `python -m evaluation.test_set`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from datasets import load_dataset

from configs.config import FineTuneConfig, get_default_config

logger = logging.getLogger("amazonqa.eval.test_set")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _flatten_row(example: dict) -> dict:
    """
    Normalise a raw `embedding-data/Amazon-QA` row.

    Expected shape: {"query": str, "pos": [str, ...]}.
    Some forks ship {"question": ..., "answers": [...]}, so we accept both.
    """
    question = (example.get("query") or example.get("question") or "").strip()
    pos = example.get("pos") or example.get("answers") or []
    answer = (pos[0] if isinstance(pos, list) and pos else "").strip()
    return {"question": question, "ground_truth_answer": answer}


def _train_indices_set(cfg: FineTuneConfig) -> set:
    """
    Reconstruct the *exact* set of dataset indices used during Phase 1 training,
    so we can subtract them from the test pool.

    `load_and_preprocess_dataset` calls:
        raw.shuffle(seed=cfg.dataset.seed).select(range(cfg.dataset.train_sample_size))
    so the training rows are the first N rows after a deterministic shuffle —
    which means we can replay the shuffle here and read out the indices.
    """
    raw = load_dataset(
        cfg.dataset.hf_dataset_id, split=cfg.dataset.hf_dataset_split
    )
    sample_size = min(cfg.dataset.train_sample_size, len(raw))
    shuffled = raw.shuffle(seed=cfg.dataset.seed)
    # `shuffle` keeps an internal index mapping accessible via `_indices` (in
    # newer `datasets` releases) — but the public, stable contract is that
    # `select(range(N))` after a shuffle picks the first N rows of that shuffle.
    # We don't need the actual original indices to *exclude* them; we only need
    # to ensure the eval shuffle uses a different seed AND skips any row whose
    # (question, answer) pair matches a training row. We do the cheaper, safer
    # thing: dedupe via question text.
    train_questions = set()
    for ex in shuffled.select(range(sample_size)):
        q = (ex.get("query") or ex.get("question") or "").strip()
        if q:
            train_questions.add(q)
    return train_questions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def build_test_set(
    cfg: Optional[FineTuneConfig] = None,
    *,
    n_samples: Optional[int] = None,
    overwrite: bool = False,
) -> pd.DataFrame:
    """
    Build (and persist) a held-out test split for RAGAS.

    Selection algorithm:
        1. Load the full HF dataset.
        2. Reconstruct the set of training-question texts (Phase 1 used a
           deterministic shuffle + select).
        3. Apply a NEW shuffle with `cfg.eval.test_set_seed` and pick the
           first `n_samples` rows whose question is NOT in the training set.
        4. Filter to non-empty (question, answer) pairs.
        5. Write to `data/test_qa.csv`.

    Args:
        cfg: Project config. Defaults to `get_default_config()`.
        n_samples: Override `cfg.eval.test_set_size`.
        overwrite: If False and the CSV exists, re-loads instead of re-building.

    Returns:
        A `pandas.DataFrame` with columns
        ['question', 'ground_truth_answer', 'context_docs', 'source_index'].
    """
    cfg = cfg or get_default_config()
    cfg.paths.ensure_all()

    n_samples = n_samples or cfg.eval.test_set_size
    out_path = cfg.paths.eval_data_dir / cfg.eval.test_set_filename

    if out_path.exists() and not overwrite:
        logger.info(
            "Test set already exists at %s (use overwrite=True to regenerate)",
            out_path,
        )
        return pd.read_csv(out_path)

    logger.info(
        "Building held-out test set: n=%d, seed=%d (≠ train seed=%d)",
        n_samples,
        cfg.eval.test_set_seed,
        cfg.dataset.seed,
    )

    # 1. Reconstruct training questions to subtract them from the eval pool.
    logger.info("Reconstructing training-question set (this can take ~1 min)...")
    train_questions = _train_indices_set(cfg)
    logger.info("Excluded %d training questions from eval pool", len(train_questions))

    # 2. Load full dataset, shuffle with EVAL seed, walk until we have n_samples.
    raw = load_dataset(
        cfg.dataset.hf_dataset_id, split=cfg.dataset.hf_dataset_split
    )
    eval_shuffled = raw.shuffle(seed=cfg.eval.test_set_seed)

    rows = []
    seen_questions = set()
    for src_idx, example in enumerate(eval_shuffled):
        if len(rows) >= n_samples:
            break
        flat = _flatten_row(example)
        q, a = flat["question"], flat["ground_truth_answer"]

        # Skip empties and short noise
        if len(q) < 5 or len(a) < 5:
            continue
        # Skip training overlap
        if q in train_questions:
            continue
        # Dedupe within the eval set itself
        if q in seen_questions:
            continue
        seen_questions.add(q)

        rows.append(
            {
                "question": q,
                "ground_truth_answer": a,
                "context_docs": "",      # filled at runtime by the RAG retriever
                "source_index": src_idx,
            }
        )

    if len(rows) < n_samples:
        logger.warning(
            "Only %d eligible rows found (requested %d). Increase the dataset "
            "or relax the filter.",
            len(rows),
            n_samples,
        )

    df = pd.DataFrame(rows)

    # 3. Persist
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    logger.info("Wrote %d test-set rows to %s", len(df), out_path)
    return df


def load_test_set(
    cfg: Optional[FineTuneConfig] = None,
    *,
    n_samples: Optional[int] = None,
) -> pd.DataFrame:
    """
    Load the persisted test set (building it if it doesn't exist yet).

    If `n_samples` is given AND smaller than the saved file, returns just the
    first `n_samples` rows — handy for `--smoke-test`.
    """
    cfg = cfg or get_default_config()
    out_path = cfg.paths.eval_data_dir / cfg.eval.test_set_filename
    if not out_path.exists():
        return build_test_set(cfg, n_samples=n_samples)

    df = pd.read_csv(out_path)
    if n_samples is not None and n_samples < len(df):
        df = df.head(n_samples).reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser(
        description="Build the Phase 3 held-out test set."
    )
    parser.add_argument("--n_samples", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    df = build_test_set(n_samples=args.n_samples, overwrite=args.overwrite)
    print(df.head())
    print(f"\nTotal rows: {len(df)}")


__all__ = ["build_test_set", "load_test_set"]
