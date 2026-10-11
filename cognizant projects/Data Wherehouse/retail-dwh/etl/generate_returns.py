"""Generate a synthetic returns.json file from existing sales data.

In a real project this would be a nightly extract from the returns system
(REST API, SFTP drop, Kafka topic, etc). For the demo we generate it
deterministically from staged sales so foreign keys always resolve.

Business rules used:
- ~7% of order lines get returned (industry-typical for retail)
- Return date is 3-30 days after order date
- Return reason distribution: 40% wrong size, 25% defective,
  20% not as described, 10% no longer needed, 5% other
- Refund amount = sales * random(0.85, 1.0) (restocking fees on some)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
from datetime import timedelta
from pathlib import Path

import pandas as pd

from etl.utils.db import get_engine

log = logging.getLogger(__name__)

RAW_DIR = Path(os.getenv("RAW_DIR", "data/raw"))

REASONS = [
    ("wrong_size",        0.40),
    ("defective",         0.25),
    ("not_as_described",  0.20),
    ("no_longer_needed",  0.10),
    ("other",             0.05),
]


def _weighted_choice(rng: random.Random) -> str:
    r = rng.random()
    cum = 0.0
    for reason, w in REASONS:
        cum += w
        if r <= cum:
            return reason
    return REASONS[-1][0]


def generate_returns(
    return_rate: float = 0.07,
    seed: int = 42,
    out_path: Path | None = None,
) -> Path:
    """Read staged sales, randomly generate returns, write JSON.

    Returns file schema (one JSON object per line - JSONL for streamability):
        {
          "return_id":     "R-000001",
          "order_id":      "CA-2016-152156",
          "row_id":        1,
          "product_id":    "FUR-BO-10001798",
          "customer_id":   "CG-12520",
          "return_date":   "2016-11-24",
          "reason":        "wrong_size",
          "refund_amount": 235.76,
          "quantity_returned": 1
        }
    """
    rng = random.Random(seed)
    engine = get_engine()

    sales = pd.read_sql(
        "SELECT row_id, order_id, product_id, customer_id, order_date, "
        "quantity, sales FROM staging.superstore_raw",
        engine,
    )
    sales["quantity"] = sales["quantity"].astype(int)
    sales["sales"]    = sales["sales"].astype(float)
    sales["order_date"] = pd.to_datetime(sales["order_date"])

    # sample ~return_rate of rows
    n_returns = int(len(sales) * return_rate)
    picked = sales.sample(n=n_returns, random_state=seed).reset_index(drop=True)

    records = []
    for i, r in picked.iterrows():
        days_later = rng.randint(3, 30)
        refund_pct = rng.uniform(0.85, 1.0)
        qty_ret    = 1 if r.quantity == 1 else rng.randint(1, int(r.quantity))
        records.append({
            "return_id":         f"R-{i+1:06d}",
            "order_id":          r.order_id,
            "row_id":            int(r.row_id),
            "product_id":        r.product_id,
            "customer_id":       r.customer_id,
            "return_date":       (r.order_date + timedelta(days=days_later)).strftime("%Y-%m-%d"),
            "reason":            _weighted_choice(rng),
            "refund_amount":     round(r.sales * refund_pct * (qty_ret / r.quantity), 2),
            "quantity_returned": qty_ret,
        })

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = out_path or (RAW_DIR / "returns.jsonl")
    with out.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")

    log.info("Generated %s return records -> %s", len(records), out)
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--return-rate", type=float, default=0.07)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    generate_returns(args.return_rate, args.seed)
