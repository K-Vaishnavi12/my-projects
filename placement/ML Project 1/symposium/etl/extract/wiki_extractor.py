"""Wikipedia extractor.

Pulls article text for each seed page in a topic bucket and writes a
raw JSON dump to ``data/raw/{topic}/{slug}.json`` so the transform
stage can be re-run without re-hitting Wikipedia (the "raw data lake"
in Data-Lakehouse terminology).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import wikipediaapi
from loguru import logger
from tqdm import tqdm

from symposium.config import get_settings
from symposium.etl.extract.topics import seeds_for
from symposium.utils import retry, stable_id, timed


# ------------------------------------------------------------------
# Wikipedia client
# ------------------------------------------------------------------

def _client() -> wikipediaapi.Wikipedia:
    return wikipediaapi.Wikipedia(
        user_agent="SymposiumRAG/1.0 (educational; contact: student@example.com)",
        language="en",
        extract_format=wikipediaapi.ExtractFormat.WIKI,
    )


def _slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")


# ------------------------------------------------------------------
# Extract one page
# ------------------------------------------------------------------

@retry(times=3, delay=2.0)
def _fetch_page(client: wikipediaapi.Wikipedia, title: str) -> dict[str, Any] | None:
    page = client.page(title)
    if not page.exists():
        logger.warning(f"[extract] page missing: {title}")
        return None

    text = page.text or ""
    if len(text) < 500:
        logger.warning(f"[extract] page too short (<500 chars): {title}")
        return None

    return {
        "id": stable_id("wiki", title),
        "title": page.title,
        "url": page.fullurl,
        "summary": page.summary,
        "text": text,
        "categories": list(page.categories.keys())[:25],
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }


# ------------------------------------------------------------------
# Extract one topic bucket
# ------------------------------------------------------------------

@timed("extract_topic")
def extract_topic(topic: str, out_dir: Path | None = None) -> list[Path]:
    """Fetch every seed page in ``topic`` and dump raw JSON to disk.

    Returns the list of written file paths.
    """
    settings = get_settings()
    out_dir = out_dir or (settings.raw_data_dir / topic)
    out_dir.mkdir(parents=True, exist_ok=True)

    client = _client()
    titles = seeds_for(topic)

    max_n = settings.max_articles_per_topic
    if max_n and len(titles) > max_n:
        titles = titles[:max_n]

    written: list[Path] = []
    for title in tqdm(titles, desc=f"extract:{topic}"):
        try:
            record = _fetch_page(client, title)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"[extract] '{title}' failed permanently: {exc}")
            continue
        if record is None:
            continue
        record["topic"] = topic
        path = out_dir / f"{_slugify(title)}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        written.append(path)

    logger.info(f"[extract] {topic}: {len(written)}/{len(titles)} pages saved -> {out_dir}")
    return written


def extract_topics(topics: list[str]) -> dict[str, list[Path]]:
    """Extract multiple topic buckets and return a topic -> paths map."""
    result: dict[str, list[Path]] = {}
    for t in topics:
        result[t] = extract_topic(t)
    return result
