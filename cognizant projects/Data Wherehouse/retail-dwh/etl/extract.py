"""Extract step.

Reads the raw Superstore CSV from ``data/raw/`` and produces a cleaned
Parquet file in ``data/processed/`` for the next stage. Keeping extract
separate from load makes the pipeline easier to test and replay.
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

RAW_DIR       = Path(os.getenv("RAW_DIR",       "data/raw"))
PROCESSED_DIR = Path(os.getenv("PROCESSED_DIR", "data/processed"))

EXPECTED_COLUMNS = {
    "Row ID", "Order ID", "Order Date", "Ship Date", "Ship Mode",
    "Customer ID", "Customer Name", "Segment", "Country", "City",
    "State", "Postal Code", "Region", "Product ID", "Category",
    "Sub-Category", "Product Name", "Sales", "Quantity", "Discount", "Profit",
}


def extract(source_file: str = "Superstore.csv", batch_id: str | None = None) -> Path:
    """Read the CSV, validate schema, write Parquet. Returns output path."""
    src = RAW_DIR / source_file
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    log.info("Reading %s", src)
    # Superstore.csv from Kaggle is typically latin-1 encoded
    df = pd.read_csv(src, encoding="latin-1")

    missing = EXPECTED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    # Normalise column names -> snake_case
    df.columns = (
        df.columns.str.strip()
                  .str.lower()
                  .str.replace("-", "_", regex=False)
                  .str.replace(" ", "_", regex=False)
    )

    # Superstore uses US date format M/D/YYYY -> normalise to ISO for Postgres
    for col in ("order_date", "ship_date"):
        df[col] = pd.to_datetime(df[col], format="%m/%d/%Y", errors="coerce") \
                    .dt.strftime("%Y-%m-%d")

    bad_dates = df[df["order_date"].isna() | df["ship_date"].isna()]
    if len(bad_dates):
        log.warning("%s rows had unparseable dates and will be dropped", len(bad_dates))
        df = df.dropna(subset=["order_date", "ship_date"])

    df["source_file"] = source_file
    df["batch_id"]    = batch_id or "manual"

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = PROCESSED_DIR / f"superstore_{df['batch_id'].iloc[0]}.parquet"
    df.to_parquet(out, index=False)
    log.info("Wrote %s rows -> %s", len(df), out)
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="Superstore.csv")
    ap.add_argument("--batch-id", default=None)
    args = ap.parse_args()
    extract(args.source, args.batch_id)
