from __future__ import annotations

from unittest.mock import patch

import app


def test_answer_question_base_interface():
    class FakeLLM:
        def invoke(self, prompt):
            return "Mock base answer"

    with patch("app.get_llm_cached", return_value=FakeLLM()):
        result = app.answer_question(
            "base",
            "Does this support Bluetooth?",
            use_phi2=False,
            top_k=3,
            max_new_tokens=128,
            temperature=0.3,
        )

    assert set(result.keys()) == {"answer", "contexts", "meta"}
    assert result["answer"] == "Mock base answer"
    assert result["contexts"] == []
    assert result["meta"]["system_name"] == "base"


def test_answer_question_rag_interface():
    class FakeChain:
        def invoke(self, payload):
            return {
                "result": "Mock RAG answer",
                "source_documents": [
                    type("Doc", (), {"page_content": "Context chunk 1", "metadata": {"score": 0.91}})(),
                    type("Doc", (), {"page_content": "Context chunk 2", "metadata": {"score": 0.88}})(),
                ],
            }

    with patch("app.get_rag_chain_cached", return_value=FakeChain()):
        result = app.answer_question(
            "rag_finetuned",
            "Does this support Bluetooth?",
            use_phi2=False,
            top_k=3,
            max_new_tokens=128,
            temperature=0.3,
        )

    assert result["answer"] == "Mock RAG answer"
    assert len(result["contexts"]) == 2
    assert result["meta"]["retrieved_docs"] == 2
    assert result["meta"]["scores"] == [0.91, 0.88]
