"""Common interface + DTOs for every vector-store backend."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class RetrievedChunk:
    chunk_id: str
    doc_id: str
    doc_title: str
    doc_url: str | None
    topic: str
    text: str
    persona_scores: dict[str, float]
    similarity: float
    rank: int


class VectorStore(ABC):
    """Backend-agnostic vector search."""

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        persona_key: str | None = None,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        ...

    def close(self) -> None:  # pragma: no cover - optional
        pass
