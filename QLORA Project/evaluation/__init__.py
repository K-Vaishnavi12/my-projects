"""
Phase 3 - RAGAS evaluation package.

Provides a reproducible, three-system comparison (base / rag_base / rag_finetuned)
on a held-out Amazon QA test split using the RAGAS metrics:
    - faithfulness
    - answer_relevancy
    - context_precision
    - context_recall

Public modules
--------------
    test_set    -> build_test_set, load_test_set
    generators  -> generate_answer, GeneratorRegistry
    ragas_eval  -> evaluate_system_with_ragas, run_full_evaluation
    visualize   -> plot_ragas_comparison, plot_ragas_radar

CLI entry point
---------------
    python -m evaluation.ragas_eval --system all --n_samples 100

Notes
-----
We deliberately keep this `__init__` lightweight (no eager imports) so that
`python -m evaluation.ragas_eval` doesn't double-import the submodule.
Use `from evaluation.<module> import ...` in user code.
"""

# Keep this empty by design - the submodules are imported on demand.
__all__ = [
    "test_set",
    "generators",
    "ragas_eval",
    "visualize",
]
