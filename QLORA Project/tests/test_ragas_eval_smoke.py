from __future__ import annotations

import pandas as pd

from configs.config import get_default_config
from evaluation.ragas_eval import evaluate_system_with_ragas, evaluate_single_query_with_ragas


class FakeRegistry:
    def generate(self, system_name: str, question: str):
        return {
            "system": system_name,
            "question": question,
            "answer": f"Mock answer for: {question}",
            "contexts": [f"Context for {question}"],
        }


def test_single_query_ragas_skips_without_ground_truth():
    out = evaluate_single_query_with_ragas(
        question="Does it support Bluetooth?",
        generated_answer="Yes.",
        contexts=["The product supports Bluetooth 5.0."],
        ground_truth_answer=None,
    )

    assert out["skipped"] is True
    assert out["scores"] == {}


def test_evaluate_system_with_ragas_smoke_with_mocked_backend(monkeypatch):
    cfg = get_default_config()
    qa_df = pd.DataFrame(
        {
            "question": ["Q1", "Q2", "Q3"],
            "ground_truth_answer": ["A1", "A2", "A3"],
        }
    )

    class FakeResult:
        def to_pandas(self):
            return pd.DataFrame(
                {
                    "question": ["Q1", "Q2", "Q3"],
                    "ground_truth": ["A1", "A2", "A3"],
                    "answer": ["X1", "X2", "X3"],
                    "contexts": [["C1"], ["C2"], ["C3"]],
                    "faithfulness": [0.8, 0.7, 0.9],
                    "answer_relevancy": [0.9, 0.8, 0.85],
                    "context_precision": [0.7, 0.75, 0.8],
                    "context_recall": [0.68, 0.7, 0.74],
                }
            )

    monkeypatch.setattr("evaluation.ragas_eval._build_ragas_judge", lambda cfg: (object(), object()))
    monkeypatch.setattr(
        "evaluation.ragas_eval._get_ragas_metrics",
        lambda metric_names: metric_names,
    )

    def fake_evaluate(**kwargs):
        return FakeResult()

    monkeypatch.setattr("evaluation.ragas_eval._get_ragas_evaluate_fn", lambda: fake_evaluate)

    out = evaluate_system_with_ragas(
        system_name="rag_base",
        qa_df=qa_df,
        n_samples=3,
        cfg=cfg,
        registry=FakeRegistry(),
        save_per_sample=False,
    )

    assert not out.empty
    assert out.iloc[-1]["question"] == "MEAN"
    assert "faithfulness" in out.columns
