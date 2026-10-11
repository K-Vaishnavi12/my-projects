"""Post-load data-quality checks. Fails the DAG task on any critical issue."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

from sqlalchemy import text

from etl.utils.db import get_engine

log = logging.getLogger(__name__)


@dataclass
class Check:
    name: str
    sql: str
    fail_if_gt: int = 0        # fail when returned count > this threshold


CHECKS: list[Check] = [
    Check(
        "fact_no_null_keys",
        """SELECT COUNT(*) FROM core.fact_sales
           WHERE order_date_key IS NULL
              OR customer_key   IS NULL
              OR product_key    IS NULL
              OR store_key      IS NULL""",
    ),
    Check(
        "fact_no_negative_quantity",
        "SELECT COUNT(*) FROM core.fact_sales WHERE quantity <= 0",
    ),
    Check(
        "fact_no_duplicate_grain",
        """SELECT COUNT(*) FROM (
              SELECT order_id, product_key, row_id, COUNT(*) c
              FROM core.fact_sales
              GROUP BY 1,2,3 HAVING COUNT(*) > 1
           ) t""",
    ),
    Check(
        "dim_customer_one_current_per_bk",
        """SELECT COUNT(*) FROM (
              SELECT customer_id FROM core.dim_customer
              WHERE is_current = TRUE
              GROUP BY 1 HAVING COUNT(*) > 1
           ) t""",
    ),
    Check(
        "dim_product_one_current_per_bk",
        """SELECT COUNT(*) FROM (
              SELECT product_id FROM core.dim_product
              WHERE is_current = TRUE
              GROUP BY 1 HAVING COUNT(*) > 1
           ) t""",
    ),
    Check(
        "row_count_reconciliation",
        # staging rows for this batch must equal fact rows loaded for this batch
        """SELECT ABS(
              (SELECT COUNT(*) FROM staging.superstore_raw WHERE batch_id = :batch_id)
              -
              (SELECT COUNT(*) FROM core.fact_sales      WHERE batch_id = :batch_id)
           )""",
    ),

    # ---- new checks: returns + freshness + drift ---------------------
    Check(
        "returns_fk_integrity",
        # every return must link to an existing (order_id, row_id) in fact_sales
        """SELECT COUNT(*)
           FROM staging.returns_raw r
           LEFT JOIN core.fact_sales fs
             ON fs.order_id = r.order_id
            AND fs.row_id   = r.row_id::INT
           WHERE r.batch_id = :batch_id AND fs.order_id IS NULL""",
    ),
    Check(
        "returns_refund_positive",
        "SELECT COUNT(*) FROM core.fact_returns WHERE refund_amount <= 0",
    ),
    Check(
        "returns_no_duplicate_id",
        """SELECT COUNT(*) FROM (
              SELECT return_id FROM core.fact_returns
              GROUP BY 1 HAVING COUNT(*) > 1
           ) t""",
    ),
    Check(
        "fact_freshness",
        # Warn (not fail) if newest fact row is older than 365 days.
        # For a demo dataset we tolerate up to 10 years since Superstore
        # data ends in 2017.
        """SELECT CASE WHEN (CURRENT_DATE - MAX(d.full_date)) > 365*10 THEN 1 ELSE 0 END
           FROM core.fact_sales f
           JOIN core.dim_date d ON d.date_key = f.order_date_key""",
    ),
    Check(
        "revenue_drift_anomaly",
        # Flag if today's total revenue differs from the historical daily
        # average by more than 5x (very rough anomaly signal). Uses the max
        # date in the warehouse as "today" so the check is meaningful on
        # historical data too.
        """WITH by_day AS (
              SELECT d.full_date, SUM(f.sales) AS rev
              FROM core.fact_sales f JOIN core.dim_date d ON d.date_key = f.order_date_key
              GROUP BY d.full_date
           ),
           stats AS (
              SELECT AVG(rev) AS mean_rev, MAX(full_date) AS last_dt FROM by_day
           )
           SELECT CASE
             WHEN (SELECT rev FROM by_day WHERE full_date = (SELECT last_dt FROM stats))
                  > 5 * (SELECT mean_rev FROM stats) THEN 1 ELSE 0 END""",
    ),
]


def run_checks(batch_id: str) -> None:
    engine = get_engine()
    failures: list[str] = []
    with engine.begin() as conn:
        for chk in CHECKS:
            count = conn.execute(text(chk.sql), {"batch_id": batch_id}).scalar_one()
            status = "PASS" if count <= chk.fail_if_gt else "FAIL"
            log.info("DQ %-40s %s (count=%s)", chk.name, status, count)
            conn.execute(
                text("""INSERT INTO meta.dq_check_log
                        (check_name, table_name, status, failed_rows, details)
                        VALUES (:n, :t, :s, :f, :d)"""),
                {"n": chk.name, "t": "core.fact_sales", "s": status,
                 "f": count, "d": f"batch_id={batch_id}"},
            )
            if status == "FAIL":
                failures.append(f"{chk.name} (count={count})")

    if failures:
        raise RuntimeError("Data quality FAILED: " + "; ".join(failures))


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-id", required=True)
    args = ap.parse_args()
    run_checks(args.batch_id)
