"""Extract + load returns.jsonl into staging + fact_returns.

Demonstrates:
- Reading a JSON Lines source (a common real-world format)
- Incremental loading using meta.load_watermark
- Idempotent upsert into fact table
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from etl.utils.db import get_engine

log = logging.getLogger(__name__)

RAW_DIR = Path(os.getenv("RAW_DIR", "data/raw"))


# ---------------------------------------------------------------------------
# Extract + stage
# ---------------------------------------------------------------------------

def load_returns_staging(source_file: str = "returns.jsonl", batch_id: str = "manual") -> int:
    src = RAW_DIR / source_file
    if not src.exists():
        raise FileNotFoundError(src)

    with src.open("r", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]

    df = pd.DataFrame(rows)
    df["batch_id"]   = batch_id
    df["loaded_at"]  = pd.Timestamp.utcnow().tz_localize(None)

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM staging.returns_raw WHERE batch_id = :b"),
                     {"b": batch_id})
        df.to_sql("returns_raw", conn, schema="staging",
                  if_exists="append", index=False,
                  method="multi", chunksize=1000)

    log.info("Staged %s return rows (batch=%s)", len(df), batch_id)
    return len(df)


# ---------------------------------------------------------------------------
# Load into fact_returns with incremental watermark
# ---------------------------------------------------------------------------

INSERT_FACT_RETURNS_SQL = """
INSERT INTO core.fact_returns (
    return_id, order_id, row_id,
    return_date_key, order_date_key,
    customer_key, product_key,
    quantity_returned, refund_amount, reason,
    batch_id
)
SELECT
    r.return_id,
    r.order_id,
    r.row_id::INT,
    TO_CHAR(r.return_date::DATE, 'YYYYMMDD')::INT AS return_date_key,
    fs.order_date_key,
    fs.customer_key,
    fs.product_key,
    r.quantity_returned::INT,
    r.refund_amount::NUMERIC(14,2),
    r.reason,
    r.batch_id
FROM staging.returns_raw r
-- link to the original sales line so we inherit the correct dim keys
JOIN core.fact_sales fs
  ON fs.order_id   = r.order_id
 AND fs.row_id     = r.row_id::INT
WHERE r.batch_id = :batch_id
  -- incremental: only newer than the watermark
  AND r.return_date::DATE > COALESCE(
        (SELECT last_order_date FROM meta.load_watermark
         WHERE table_name = 'core.fact_returns'),
        DATE '1900-01-01'
    )
ON CONFLICT (return_id) DO NOTHING;
"""

UPDATE_WATERMARK_SQL = """
INSERT INTO meta.load_watermark (table_name, last_loaded_at, last_order_date)
VALUES ('core.fact_returns', NOW(),
        (SELECT MAX(return_date::DATE) FROM staging.returns_raw WHERE batch_id = :batch_id))
ON CONFLICT (table_name) DO UPDATE
SET last_loaded_at = EXCLUDED.last_loaded_at,
    last_order_date = GREATEST(meta.load_watermark.last_order_date, EXCLUDED.last_order_date);
"""


def load_fact_returns(batch_id: str) -> int:
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(text(INSERT_FACT_RETURNS_SQL), {"batch_id": batch_id})
        n = result.rowcount or 0
        conn.execute(text(UPDATE_WATERMARK_SQL), {"batch_id": batch_id})
    log.info("Inserted %s rows into core.fact_returns (batch=%s)", n, batch_id)
    return n


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-id", required=True)
    args = ap.parse_args()
    load_returns_staging(batch_id=args.batch_id)
    load_fact_returns(args.batch_id)
