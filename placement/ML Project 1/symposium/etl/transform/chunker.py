"""Chunker: split a cleaned article into overlapping windows.

Wraps :func:`symposium.utils.chunk_by_sentences` with metadata:
each chunk carries its source document id, position, extracted years,
and pre-computed persona affinity scores.
"""

from __future__ import annotations

from typing import Any, Iterator

from symposium.config import get_settings
from symposium.etl.transform.persona_classifier import features_and_scores
from symposium.utils import chunk_by_sentences, extract_years, stable_id


def chunk_article(article: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Yield one chunk dict per window of the cleaned article."""
    s = get_settings()
    text = article["clean_text"]
    doc_id = article["id"]

    for position, chunk_text in enumerate(
        chunk_by_sentences(text, s.chunk_size, s.chunk_overlap)
    ):
        fs = features_and_scores(chunk_text)
        yield {
            "chunk_id": stable_id(doc_id, str(position)),
            "doc_id": doc_id,
            "doc_title": article["title"],
            "doc_url": article.get("url"),
            "topic": article.get("topic"),
            "position": position,
            "text": chunk_text,
            "char_len": len(chunk_text),
            "years": extract_years(chunk_text),
            "features": fs["features"],
            "persona_scores": fs["persona_scores"],
        }
