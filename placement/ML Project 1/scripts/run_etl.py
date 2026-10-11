"""Run the full ETL pipeline.

Usage:
    python scripts/run_etl.py --topics history science
    python scripts/run_etl.py --topics all
    python scripts/run_etl.py --topics history --skip-extract  # reuse raw dumps
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running as `python scripts/run_etl.py`
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from loguru import logger

from symposium.etl.pipeline import run_pipeline
from symposium.etl.extract.topics import available_topics


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Symposium ETL pipeline")
    parser.add_argument(
        "--topics",
        nargs="+",
        default=["history"],
        help="Topic buckets to load. Use 'all' to run every bucket.",
    )
    parser.add_argument(
        "--skip-extract",
        action="store_true",
        help="Skip the Wikipedia fetch and reuse whatever is already in data/raw/",
    )
    args = parser.parse_args()

    topics = args.topics
    if len(topics) == 1 and topics[0] == "all":
        topics = available_topics()

    logger.info(f"Running ETL for topics: {topics}")
    stats = run_pipeline(topics, skip_extract=args.skip_extract)
    logger.success("Done.")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
