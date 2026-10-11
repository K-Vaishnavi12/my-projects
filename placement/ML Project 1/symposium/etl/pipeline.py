"""ETL orchestrator.

Runs the four canonical stages end-to-end for one or more topic
buckets:

    extract -> clean -> chunk -> embed -> load(mongo + sqlite)

Every stage is a plain function so this file also serves as
executable *documentation* of the pipeline. In production you'd swap
this for an Airflow DAG (see ``docs/ARCHITECTURE.md``).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from loguru import logger
from tqdm import tqdm

from symposium.config import get_settings
from symposium.etl.extract.wiki_extractor import extract_topics
from symposium.etl.load.mongo_loader import MongoLoader
from symposium.etl.load.sqlite_loader import SqliteLoader
from symposium.etl.transform.chunker import chunk_article
from symposium.etl.transform.cleaner import clean_article
from symposium.etl.transform.embedder import Embedder, get_embedder
from symposium.utils import batched, timed, write_json


# ------------------------------------------------------------------
# Stage helpers
# ------------------------------------------------------------------

def _iter_raw_articles(topic_paths: dict[str, list[Path]]) -> Iterable[dict[str, Any]]:
    for topic, paths in topic_paths.items():
        for p in paths:
            with p.open("r", encoding="utf-8") as f:
                article = json.load(f)
            article["topic"] = topic
            yield article


def _clean_stream(articles: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for a in articles:
        try:
            yield clean_article(a)
        except ValueError as exc:
            logger.warning(f"[clean] skip: {exc}")


def _stage_articles_to_disk(
    articles: Iterable[dict[str, Any]],
    staging_dir: Path,
) -> list[dict[str, Any]]:
    """Materialise cleaned articles into the staging layer.

    Represents the "staging" area in the Data Lakehouse pattern.
    We keep them on disk (and could push to S3) so downstream
    steps are re-runnable without going back to Wikipedia.
    """
    staging_dir.mkdir(parents=True, exist_ok=True)
    kept: list[dict[str, Any]] = []
    for a in articles:
        write_json(staging_dir / f"{a['id']}.json", a)
        kept.append(a)
    logger.info(f"[stage] staged {len(kept)} cleaned articles -> {staging_dir}")
    return kept


# ------------------------------------------------------------------
# Load helpers
# ------------------------------------------------------------------

def _load_documents_and_chunks(
    articles: list[dict[str, Any]],
    embedder: Embedder,
    mongo: MongoLoader,
    sql: SqliteLoader,
) -> tuple[int, int]:
    total_docs = 0
    total_chunks = 0

    for a in tqdm(articles, desc="load-articles"):
        # 1. dimensional writes
        sql.seed_topic(a["topic"])
        sql.upsert_document(a)
        mongo.upsert_document(a)
        total_docs += 1

        # 2. chunk + embed
        chunks = list(chunk_article(a))
        if not chunks:
            continue
        texts = [c["text"] for c in chunks]
        embeddings = embedder.encode(texts, batch_size=32).tolist()

        # 3. fact writes (SQL + Mongo)
        sql.upsert_chunks(chunks)
        mongo.upsert_chunks(chunks, embeddings)
        total_chunks += len(chunks)

    return total_docs, total_chunks


# ------------------------------------------------------------------
# Orchestrator
# ------------------------------------------------------------------

@timed("run_pipeline")
def run_pipeline(topics: list[str], skip_extract: bool = False) -> dict[str, Any]:
    """Run the whole ETL for the requested topic buckets.

    Args:
        topics: e.g. ``["history", "science"]``
        skip_extract: if True, reuse whatever is already under
            ``data/raw/`` (useful for iterating on the transform step).

    Returns a small stats dict for logging / UI display.
    """
    settings = get_settings()

    # ---- 1. Extract ----
    if skip_extract:
        topic_paths = {
            t: sorted((settings.raw_data_dir / t).glob("*.json"))
            for t in topics
        }
        logger.info(f"[extract] skipped; using cached raw data")
    else:
        topic_paths = extract_topics(topics)

    total_raw = sum(len(v) for v in topic_paths.values())
    logger.info(f"[extract] total raw articles available: {total_raw}")

    # ---- 2. Clean + stage ----
    raw_stream = _iter_raw_articles(topic_paths)
    cleaned_stream = _clean_stream(raw_stream)
    staged = _stage_articles_to_disk(cleaned_stream, settings.staging_data_dir)

    # ---- 3. Load into DWH + Mongo ----
    mongo = MongoLoader()
    mongo.ensure_collections()

    sql = SqliteLoader()
    sql.apply_schema()
    sql.seed_personas()

    embedder = get_embedder()
    docs, chunks = _load_documents_and_chunks(staged, embedder, mongo, sql)

    # ---- 4. Vector indexes (best-effort on non-Atlas deploys) ----
    mongo.ensure_vector_index()

    stats = {
        "topics": topics,
        "raw_articles": total_raw,
        "staged_articles": len(staged),
        "loaded_documents": docs,
        "loaded_chunks": chunks,
    }
    logger.success(f"[pipeline] done: {stats}")

    mongo.close()
    sql.close()
    return stats
