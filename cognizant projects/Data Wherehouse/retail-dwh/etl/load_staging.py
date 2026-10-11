"""Load the processed Parquet file into ``staging.superstore_raw``.

Truncates the staging table for the current batch before insert so the
step is idempotent.
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from etl.utils.db import get_engine

log = logging.getLogger(__name__)

PROCESSED_DIR = Path(os.getenv("PROCESSED_DIR", "data/processed"))

STAGING_COLUMNS = [
    "row_id", "order_id", "order_date", "ship_date", "ship_mode",
    "customer_id", "customer_name", "segment", "country", "city",
    "state", "postal_code", "region", "product_id", "category",
    "sub_category", "product_name", "sales", "quantity", "discount", "profit",
    "source_file", "batch_id",
]


def load_staging(parquet_path: str) -> int:
    p = Path(parquet_path)
    if not p.exists():
        raise FileNotFoundError(p)

    df = pd.read_parquet(p)
    df = df[[c for c in STAGING_COLUMNS if c in df.columns]]
    # Everything goes in as text; cast to string to be safe
    df = df.astype(str)

    batch_id = df["batch_id"].iloc[0]
    engine = get_engine()
    with engine.begin() as conn:
        log.info("Clearing prior rows for batch_id=%s", batch_id)
        conn.execute(
            text("DELETE FROM staging.superstore_raw WHERE batch_id = :b"),
            {"b": batch_id},
        )
        df.to_sql(
            "superstore_raw",
            conn,
            schema="staging",
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )
    log.info("Loaded %s rows into staging.superstore_raw", len(df))
    return len(df)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("parquet_path")
    args = ap.parse_args()
    load_staging(args.parquet_path)
