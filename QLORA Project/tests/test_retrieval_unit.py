from __future__ import annotations

from typing import List

import pytest

try:
    from langchain.schema import Document
    from configs.config import get_default_config
    from src.rag_pipeline import build_retriever
except Exception as exc:  # pragma: no cover - dependency/environment guard
    pytestmark = pytest.mark.skip(reason=f"retrieval deps unavailable: {exc}")


class FakeVectorStore:
    def __init__(self, docs: List[Document]):
        self.docs = docs

    def as_retriever(self, search_type="similarity", search_kwargs=None):
        docs = self.docs

        class _Retriever:
            def __init__(self, docs_):
                self.docs_ = docs_

            def invoke(self, query):
                query_l = query.lower()
                ranked = [d for d in self.docs_ if any(tok in d.page_content.lower() for tok in query_l.split())]
                return ranked or self.docs_[:1]

        return _Retriever(docs)


def test_build_retriever_returns_non_empty_results():
    cfg = get_default_config()
    cfg.rag.top_k = 2

    docs = [
        Document(page_content="Question: Is the mouse wireless? Answer: Yes, it is wireless."),
        Document(page_content="Question: Does the keyboard have backlight? Answer: Yes, white backlight."),
    ]
    retriever = build_retriever(FakeVectorStore(docs), cfg)
    out = retriever.invoke("wireless mouse")

    assert out
    assert any("wireless" in doc.page_content.lower() for doc in out)
