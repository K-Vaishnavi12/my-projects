"""SQLite loader for the SQL data warehouse.

Applies the DDL from ``symposium/dwh/sql/`` on startup, then upserts:
- ``dim_document``     - one row per source article
- ``dim_topic``        - one row per topic bucket
- ``dim_persona``      - one row per persona (seeded from the registry)
- ``fact_chunk``       - one row per chunk with feature columns

The debate-time facts (``fact_query``, ``fact_turn``, ``fact_retrieval``)
are populated at debate runtime by :mod:`symposium.agents.recorder`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from loguru import logger

from symposium.config import get_settings
from symposium.config.personas import PERSONAS


SQL_DIR = Path(__file__).resolve().parents[2] / "dwh" / "sql"


class SqliteLoader:
    """Manages the SQLite DWH connection + writes."""

    def __init__(self, db_path: Path | None = None) -> None:
        s = get_settings()
        self.db_path = db_path or s.sqlite_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA foreign_keys=ON;")
        self.conn.row_factory = sqlite3.Row

    # --------------------------------------------------------------
    # Schema
    # --------------------------------------------------------------

    def apply_schema(self) -> None:
        """Run the DDL / seed / views / triggers scripts.

        We deliberately skip the ``04_*`` file - that's a reference
        query library for the reviewer, not something to execute at
        load time.
        """
        files = [
            p for p in sorted(SQL_DIR.glob("[0-9]*.sql"))
            if not p.stem.startswith("04_")
        ]
        if not files:
            raise FileNotFoundError(f"No DDL files under {SQL_DIR}")
        for f in files:
            sql = f.read_text(encoding="utf-8")
            logger.info(f"[sqlite] applying {f.name} ({len(sql):,} chars)")
            self.conn.executescript(sql)
        self.conn.commit()

    def seed_personas(self) -> None:
        rows = [(p.key, p.name, p.tagline, p.color) for p in PERSONAS.values()]
        self.conn.executemany(
            """
            INSERT INTO dim_persona(persona_key, name, tagline, color)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(persona_key) DO UPDATE SET
                name=excluded.name,
                tagline=excluded.tagline,
                color=excluded.color
            """,
            rows,
        )
        self.conn.commit()

    def seed_topic(self, topic: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO dim_topic(topic_key) VALUES(?)", (topic,)
        )
        self.conn.commit()

    # --------------------------------------------------------------
    # Dimension writes
    # --------------------------------------------------------------

    def upsert_document(self, article: dict) -> None:
        self.conn.execute(
            """
            INSERT INTO dim_document(
                doc_id, title, url, topic_key, summary, extracted_at
            ) VALUES(?, ?, ?, ?, ?, ?)
            ON CONFLICT(doc_id) DO UPDATE SET
                title=excluded.title,
                url=excluded.url,
                topic_key=excluded.topic_key,
                summary=excluded.summary,
                extracted_at=excluded.extracted_at
            """,
            (
                article["id"],
                article["title"],
                article.get("url"),
                article.get("topic"),
                article.get("summary"),
                article.get("extracted_at"),
            ),
        )
        self.conn.commit()

    def upsert_chunks(self, chunks: Iterable[dict]) -> int:
        chunks = list(chunks)
        rows = []
        for c in chunks:
            f = c["features"]
            ps = c["persona_scores"]
            rows.append((
                c["chunk_id"],
                c["doc_id"],
                c["position"],
                c["char_len"],
                len(c["years"]),
                f["date_density"],
                f["evidence_density"],
                f["narrative_density"],
                f["counter_density"],
                f["reading_ease"],
                f["avg_word_len"],
                ps.get("historian", 0.0),
                ps.get("scientist", 0.0),
                ps.get("poet", 0.0),
                ps.get("skeptic", 0.0),
                ps.get("child", 0.0),
            ))
        self.conn.executemany(
            """
            INSERT INTO fact_chunk(
                chunk_id, doc_id, position, char_len, year_count,
                date_density, evidence_density, narrative_density,
                counter_density, reading_ease, avg_word_len,
                score_historian, score_scientist, score_poet,
                score_skeptic, score_child
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(chunk_id) DO UPDATE SET
                char_len=excluded.char_len,
                year_count=excluded.year_count,
                date_density=excluded.date_density,
                evidence_density=excluded.evidence_density,
                narrative_density=excluded.narrative_density,
                counter_density=excluded.counter_density,
                reading_ease=excluded.reading_ease,
                avg_word_len=excluded.avg_word_len,
                score_historian=excluded.score_historian,
                score_scientist=excluded.score_scientist,
                score_poet=excluded.score_poet,
                score_skeptic=excluded.score_skeptic,
                score_child=excluded.score_child
            """,
            rows,
        )
        self.conn.commit()
        return len(rows)

    # --------------------------------------------------------------
    # Debate-time writes (called from agents.recorder)
    # --------------------------------------------------------------

    def start_query(self, query_id: str, question: str, topic: str | None) -> None:
        self.conn.execute(
            """
            INSERT INTO fact_query(query_id, question, topic_key, started_at)
            VALUES(?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(query_id) DO NOTHING
            """,
            (query_id, question, topic),
        )
        self.conn.commit()

    def finish_query(
        self,
        query_id: str,
        consensus_score: float,
        moderator_summary: str,
    ) -> None:
        self.conn.execute(
            """
            UPDATE fact_query
               SET ended_at = CURRENT_TIMESTAMP,
                   consensus_score = ?,
                   moderator_summary = ?
             WHERE query_id = ?
            """,
            (consensus_score, moderator_summary, query_id),
        )
        self.conn.commit()

    def insert_turn(self, turn: dict) -> None:
        self.conn.execute(
            """
            INSERT INTO fact_turn(
                turn_id, query_id, persona_key, turn_index,
                content, tokens, stance_label, stance_score,
                agreement_score, latency_ms
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                turn["turn_id"],
                turn["query_id"],
                turn["persona_key"],
                turn["turn_index"],
                turn["content"],
                turn.get("tokens", 0),
                turn.get("stance_label"),
                turn.get("stance_score"),
                turn.get("agreement_score"),
                turn.get("latency_ms", 0),
            ),
        )
        self.conn.commit()

    def insert_retrievals(self, rows: list[dict]) -> None:
        if not rows:
            return
        payload = [
            (
                r["turn_id"],
                r["chunk_id"],
                r["rank"],
                r["similarity"],
            )
            for r in rows
        ]
        self.conn.executemany(
            """
            INSERT INTO fact_retrieval(turn_id, chunk_id, rank, similarity)
            VALUES(?, ?, ?, ?)
            """,
            payload,
        )
        self.conn.commit()

    # --------------------------------------------------------------
    # Housekeeping
    # --------------------------------------------------------------

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
