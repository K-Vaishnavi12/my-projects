"""SQL-warehouse accessor.

Provides:
- Named "stored-procedure-equivalent" methods (Python callables backed
  by parameterised SQL) - a common pattern for SQLite where true
  stored procs don't exist.
- CSV export for Power BI.
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

from symposium.config import get_settings


class Warehouse:
    """Read + admin façade over the SQLite DWH."""

    def __init__(self, db_path: Path | None = None) -> None:
        s = get_settings()
        self.db_path = db_path or s.sqlite_path

        # Ensure schema exists on first use (Streamlit Cloud starts empty).
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        needs_bootstrap = not self.db_path.exists() or self.db_path.stat().st_size == 0
        logger.info(
            f"[warehouse] db={self.db_path} exists={self.db_path.exists()} "
            f"size={self.db_path.stat().st_size if self.db_path.exists() else 0} "
            f"needs_bootstrap={needs_bootstrap}"
        )

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")

        if needs_bootstrap:
            self._bootstrap_schema()

    def _bootstrap_schema(self) -> None:
        """Apply the DDL scripts so we always have tables to query."""
        try:
            from symposium.etl.load.sqlite_loader import SqliteLoader, SQL_DIR
            logger.info(f"[warehouse] applying DDL from {SQL_DIR}")
            loader = SqliteLoader(self.db_path)
            loader.apply_schema()
            loader.seed_personas()
            loader.close()
            logger.success(f"[warehouse] schema bootstrapped OK")
        except Exception as exc:  # noqa: BLE001
            logger.error(f"[warehouse] bootstrap failed: {type(exc).__name__}: {exc}")

    # --------------------------------------------------------------
    # Generic helpers
    # --------------------------------------------------------------

    def query(self, sql: str, params: tuple = ()) -> pd.DataFrame:
        """Return any SELECT as a Pandas DataFrame.

        Returns an empty DataFrame if the query fails (e.g. table
        missing on first boot) so callers don't crash.
        """
        try:
            return pd.read_sql_query(sql, self.conn, params=params)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[warehouse.query] failed ({exc}); returning empty DF")
            return pd.DataFrame()

    def scalar(self, sql: str, params: tuple = ()) -> Any:
        try:
            cur = self.conn.execute(sql, params)
            row = cur.fetchone()
            return row[0] if row else None
        except sqlite3.OperationalError:
            return None

    # --------------------------------------------------------------
    # "Stored procedures" (parameterised, business-named)
    # --------------------------------------------------------------

    def sp_topic_summary(self, topic_key: str) -> pd.DataFrame:
        return self.query(
            """
            SELECT  d.title,
                    COUNT(c.chunk_id) AS chunks,
                    AVG(c.evidence_density) AS avg_evidence,
                    AVG(c.narrative_density) AS avg_narrative
            FROM    fact_chunk c
            JOIN    dim_document d USING (doc_id)
            WHERE   d.topic_key = ?
            GROUP   BY d.title
            ORDER   BY chunks DESC
            """,
            (topic_key,),
        )

    def sp_persona_leaderboard(self) -> pd.DataFrame:
        return self.query("SELECT * FROM v_persona_activity ORDER BY total_turns DESC")

    def sp_recent_debates(self, limit: int = 20) -> pd.DataFrame:
        return self.query(
            """
            SELECT  q.query_id, q.question, q.topic_key,
                    q.consensus_score, q.started_at
            FROM    fact_query q
            ORDER   BY q.started_at DESC
            LIMIT   ?
            """,
            (limit,),
        )

    def sp_evidence_for_query(self, query_id: str) -> pd.DataFrame:
        return self.query(
            """
            SELECT  turn_id, persona_key, turn_index,
                    evidence_rank, similarity, source_title, source_url
            FROM    v_debate_evidence_trail
            WHERE   query_id = ?
            ORDER   BY turn_index, evidence_rank
            """,
            (query_id,),
        )

    def sp_rolling_consensus(self, topic_key: str) -> pd.DataFrame:
        return self.query(
            """
            SELECT  query_id, started_at, consensus_score,
                    AVG(consensus_score) OVER (
                        ORDER BY started_at
                        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                    ) AS rolling5
            FROM    fact_query
            WHERE   topic_key = ? AND consensus_score IS NOT NULL
            ORDER   BY started_at
            """,
            (topic_key,),
        )

    def sp_chunk_persona_top(self, persona_key: str, n: int = 20) -> pd.DataFrame:
        col = f"score_{persona_key}"
        return self.query(
            f"""
            SELECT  c.chunk_id, d.title, d.topic_key, c.{col} AS affinity
            FROM    fact_chunk c
            JOIN    dim_document d USING (doc_id)
            ORDER   BY c.{col} DESC
            LIMIT   ?
            """,
            (n,),
        )

    # --------------------------------------------------------------
    # Utilities
    # --------------------------------------------------------------

    def counts(self) -> dict[str, int]:
        tables = [
            "dim_topic", "dim_persona", "dim_document",
            "fact_chunk", "fact_query", "fact_turn", "fact_retrieval",
        ]
        out: dict[str, int] = {}
        for t in tables:
            try:
                out[t] = self.scalar(f"SELECT COUNT(*) FROM {t}") or 0
            except sqlite3.OperationalError:
                # Table doesn't exist yet (e.g. first boot on Streamlit Cloud)
                out[t] = 0
        return out

    def export_all_csv(self, out_dir: Path | None = None) -> list[Path]:
        """Dump every dim + fact table to CSV for Power BI."""
        s = get_settings()
        out_dir = out_dir or s.export_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        tables = [
            "dim_topic", "dim_persona", "dim_document",
            "fact_chunk", "fact_query", "fact_turn", "fact_retrieval",
            "v_persona_activity", "v_topic_debate_stats",
            "v_debate_evidence_trail",
        ]
        written: list[Path] = []
        for t in tables:
            try:
                df = self.query(f"SELECT * FROM {t}")
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"[export] skipping {t}: {exc}")
                continue
            path = out_dir / f"{t}.csv"
            df.to_csv(path, index=False)
            written.append(path)
            logger.info(f"[export] {t} -> {path} ({len(df)} rows)")
        return written

    def close(self) -> None:
        self.conn.close()
