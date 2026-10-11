"""Load ``core.fact_sales`` from staging.

Resolves surrogate keys for SCD2 dims **as of the order date** so historical
facts point at the correct historical dim version.
Idempotent: uses ON CONFLICT on the natural key (order_id, product_key, row_id).
"""

from __future__ import annotations

import logging

from sqlalchemy import text

from etl.utils.db import get_engine

log = logging.getLogger(__name__)


INSERT_FACT_SQL = """
INSERT INTO core.fact_sales (
    order_id, row_id,
    order_date_key, ship_date_key,
    customer_key, product_key, store_key, ship_mode_key,
    quantity, sales, discount, profit,
    batch_id
)
SELECT
    s.order_id,
    s.row_id::INT,

    TO_CHAR(s.order_date::DATE, 'YYYYMMDD')::INT           AS order_date_key,
    TO_CHAR(s.ship_date::DATE,  'YYYYMMDD')::INT           AS ship_date_key,

    dc.customer_key,
    dp.product_key,
    ds.store_key,
    dsm.ship_mode_key,

    s.quantity::INT,
    s.sales::NUMERIC(14,2),
    s.discount::NUMERIC(6,4),
    s.profit::NUMERIC(14,2),

    s.batch_id
FROM staging.superstore_raw s

-- resolve SCD2 customer_key valid at order_date
JOIN core.dim_customer dc
  ON dc.customer_id  = s.customer_id
 AND s.order_date::TIMESTAMP >= dc.effective_from
 AND s.order_date::TIMESTAMP <  dc.effective_to

-- resolve SCD2 product_key valid at order_date
JOIN core.dim_product dp
  ON dp.product_id   = s.product_id
 AND s.order_date::TIMESTAMP >= dp.effective_from
 AND s.order_date::TIMESTAMP <  dp.effective_to

JOIN core.dim_store ds
  ON ds.country     = s.country
 AND ds.region      = s.region
 AND ds.state       = s.state
 AND ds.city        = s.city
 AND ds.postal_code = s.postal_code

JOIN core.dim_ship_mode dsm
  ON dsm.ship_mode  = s.ship_mode

WHERE s.batch_id = :batch_id

ON CONFLICT (order_id, product_key, row_id) DO NOTHING;
"""


def load_fact_sales(batch_id: str) -> int:
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(text(INSERT_FACT_SQL), {"batch_id": batch_id})
        n = result.rowcount or 0
    log.info("Inserted %s rows into core.fact_sales for batch_id=%s", n, batch_id)
    return n


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-id", required=True)
    args = ap.parse_args()
    load_fact_sales(args.batch_id)
