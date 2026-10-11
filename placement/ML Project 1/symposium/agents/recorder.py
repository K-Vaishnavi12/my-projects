"""Debate recorder.

Persists every debate to the SQL DWH so the analytics dashboards
have real data to slice.
"""

from __future__ import annotations

import uuid
from typing import Any

from symposium.dwh.warehouse import Warehouse
from symposium.etl.load.sqlite_loader import SqliteLoader


class DebateRecorder:
    """Thin write-only wrapper on top of :class:`SqliteLoader`."""

    def __init__(self) -> None:
        self.sql = SqliteLoader()

    def start_debate(self, question: str, topic: str | None) -> str:
        query_id = str(uuid.uuid4())
        self.sql.start_query(query_id, question, topic)
        return query_id

    def record_turn(
        self,
        *,
        query_id: str,
        turn_id: str,
        persona_key: str,
        turn_index: int,
        content: str,
        stance_label: str | None,
        stance_score: float | None,
        agreement_score: float | None,
        latency_ms: int,
        retrievals: list[dict],
    ) -> None:
        self.sql.insert_turn({
            "turn_id": turn_id,
            "query_id": query_id,
            "persona_key": persona_key,
            "turn_index": turn_index,
            "content": content,
            "tokens": len(content.split()),
            "stance_label": stance_label,
            "stance_score": stance_score,
            "agreement_score": agreement_score,
            "latency_ms": latency_ms,
        })
        self.sql.insert_retrievals(retrievals)

    def finish_debate(self, query_id: str, consensus_score: float, summary: str) -> None:
        self.sql.finish_query(query_id, consensus_score, summary)

    def close(self) -> None:
        self.sql.close()
