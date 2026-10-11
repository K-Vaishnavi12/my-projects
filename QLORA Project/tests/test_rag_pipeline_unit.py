from __future__ import annotations

import pytest

try:
    from langchain.schema import Document
    from configs.config import get_default_config
    from src.rag_pipeline import chunk_documents
except Exception as exc:  # pragma: no cover - dependency/environment guard
    pytestmark = pytest.mark.skip(reason=f"rag pipeline deps unavailable: {exc}")


def test_chunk_documents_splits_long_text():
    cfg = get_default_config()
    cfg.rag.chunk_size = 60
    cfg.rag.chunk_overlap = 10

    docs = [
        Document(
            page_content=(
                "Question: Does this speaker support Bluetooth pairing?\n"
                "Answer: Yes, it supports Bluetooth and can pair with multiple devices. "
                "It also supports wired audio input for compatible hardware."
            )
        )
    ]

    chunks = chunk_documents(docs, cfg)

    assert len(chunks) >= 2
    assert all(len(chunk.page_content) <= 60 for chunk in chunks)


def test_chunk_documents_preserves_content_signal():
    cfg = get_default_config()
    cfg.rag.chunk_size = 80
    cfg.rag.chunk_overlap = 10

    docs = [Document(page_content="Question: Is it waterproof?\nAnswer: No, it is splash-resistant only.")]
    chunks = chunk_documents(docs, cfg)

    joined = " ".join(chunk.page_content for chunk in chunks)
    assert "waterproof" in joined.lower()
    assert "splash-resistant" in joined.lower()
