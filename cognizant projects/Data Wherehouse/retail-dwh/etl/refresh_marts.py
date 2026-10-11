"""Refresh the pre-aggregated marts after fact loads.

Each function is idempotent: truncate + insert. Called from the DAG after
fact_sales and fact_returns are loaded so the marts always reflect the
latest data.
"""

from __future__ import annotations

import logging

from sqlalchemy import text

from etl.utils.db import get_engine

log = logging.getLogger(__name__)


REFRESH_SALES_DAILY_SQL = """
TRUNCATE TABLE marts.mart_sales_daily;
INSERT INTO marts.mart_sales_daily (
    order_date, region, orders, units, revenue, profit,
    profit_margin, avg_discount, avg_order_value
)
SELECT
    d.full_date                                     AS order_date,
    ds.region,
    COUNT(DISTINCT f.order_id)                      AS orders,
    SUM(f.quantity)                                 AS units,
    SUM(f.sales)                                    AS revenue,
    SUM(f.profit)                                   AS profit,
    ROUND(SUM(f.profit) / NULLIF(SUM(f.sales),0), 4) AS profit_margin,
    ROUND(AVG(f.discount), 4)                       AS avg_discount,
    ROUND(SUM(f.sales) / NULLIF(COUNT(DISTINCT f.order_id),0), 2) AS avg_order_value
FROM core.fact_sales f
JOIN core.dim_date   d  ON d.date_key   = f.order_date_key
JOIN core.dim_store  ds ON ds.store_key = f.store_key
GROUP BY d.full_date, ds.region;
"""


REFRESH_CUSTOMER_360_SQL = """
TRUNCATE TABLE marts.mart_customer_360;

WITH sales AS (
    SELECT
        dc.customer_id,
        MAX(dc.customer_name)                         AS customer_name,
        MAX(dc.segment)                               AS segment,
        MIN(d.full_date)                              AS first_order_date,
        MAX(d.full_date)                              AS last_order_date,
        COUNT(DISTINCT f.order_id)                    AS total_orders,
        SUM(f.quantity)                               AS total_units,
        SUM(f.sales)                                  AS lifetime_revenue,
        SUM(f.profit)                                 AS lifetime_profit
    FROM core.fact_sales f
    JOIN core.dim_customer dc ON dc.customer_key = f.customer_key AND dc.is_current
    JOIN core.dim_date     d  ON d.date_key      = f.order_date_key
    GROUP BY dc.customer_id
),
returns AS (
    SELECT
        dc.customer_id,
        COUNT(*)                                      AS total_returns,
        SUM(fr.refund_amount)                         AS total_refunded
    FROM core.fact_returns fr
    JOIN core.dim_customer dc ON dc.customer_key = fr.customer_key AND dc.is_current
    GROUP BY dc.customer_id
),
rfm_base AS (
    SELECT
        customer_id,
        (CURRENT_DATE - last_order_date)              AS recency_days,
        total_orders                                  AS frequency,
        lifetime_revenue                              AS monetary
    FROM sales
),
rfm_scored AS (
    SELECT
        customer_id, recency_days, frequency, monetary,
        NTILE(5) OVER (ORDER BY recency_days DESC)    AS r_score,
        NTILE(5) OVER (ORDER BY frequency)            AS f_score,
        NTILE(5) OVER (ORDER BY monetary)             AS m_score
    FROM rfm_base
)
INSERT INTO marts.mart_customer_360 (
    customer_id, customer_name, segment,
    first_order_date, last_order_date,
    total_orders, total_units, lifetime_revenue, lifetime_profit, avg_order_value,
    total_returns, total_refunded, return_rate,
    recency_days, frequency, monetary,
    r_score, f_score, m_score, rfm_segment
)
SELECT
    s.customer_id, s.customer_name, s.segment,
    s.first_order_date, s.last_order_date,
    s.total_orders, s.total_units, s.lifetime_revenue, s.lifetime_profit,
    ROUND(s.lifetime_revenue / NULLIF(s.total_orders,0), 2)         AS avg_order_value,
    COALESCE(r.total_returns, 0),
    COALESCE(r.total_refunded, 0),
    ROUND(COALESCE(r.total_returns,0)::NUMERIC / NULLIF(s.total_orders,0), 4) AS return_rate,
    rfm.recency_days, rfm.frequency, rfm.monetary,
    rfm.r_score, rfm.f_score, rfm.m_score,
    CASE
        WHEN rfm.r_score >= 4 AND rfm.f_score >= 4 AND rfm.m_score >= 4 THEN 'Champions'
        WHEN rfm.r_score >= 4 AND rfm.f_score >= 3                      THEN 'Loyal'
        WHEN rfm.r_score >= 4                                           THEN 'New / Promising'
        WHEN rfm.r_score <= 2 AND rfm.f_score >= 4                      THEN 'At Risk'
        WHEN rfm.r_score <= 2 AND rfm.m_score >= 4                      THEN 'Cant Lose Them'
        WHEN rfm.r_score <= 2                                           THEN 'Hibernating'
        ELSE 'Needs Attention'
    END                                                                 AS rfm_segment
FROM sales s
LEFT JOIN returns r ON r.customer_id = s.customer_id
LEFT JOIN rfm_scored rfm ON rfm.customer_id = s.customer_id;
"""


REFRESH_INVENTORY_SQL = """
TRUNCATE TABLE marts.mart_inventory;

WITH last90 AS (
    -- rolling 90 days relative to the max order date in the warehouse
    SELECT MAX(full_date) AS max_dt
    FROM core.dim_date d
    JOIN core.fact_sales f ON f.order_date_key = d.date_key
),
demand AS (
    SELECT
        dp.product_id,
        MAX(dp.product_name)   AS product_name,
        MAX(dp.category)       AS category,
        MAX(dp.sub_category)   AS sub_category,
        SUM(f.quantity)        AS units_sold_90d,
        SUM(f.sales)           AS revenue_90d
    FROM core.fact_sales f
    JOIN core.dim_product dp ON dp.product_key = f.product_key
    JOIN core.dim_date    d  ON d.date_key     = f.order_date_key
    JOIN last90 lw ON TRUE
    WHERE d.full_date >= lw.max_dt - INTERVAL '90 days'
    GROUP BY dp.product_id
),
sim AS (
    -- Simulate on-hand stock deterministically from product_id hash.
    -- Real projects would join a real inventory feed here.
    SELECT
        d.*,
        ROUND(d.units_sold_90d / 90.0, 2)                              AS avg_daily_demand,
        (ABS(HASHTEXT(d.product_id)) % 4 + 1) * GREATEST(d.units_sold_90d, 1) / 3 AS on_hand_raw
    FROM demand d
)
INSERT INTO marts.mart_inventory (
    product_id, product_name, category, sub_category,
    units_sold_90d, avg_daily_demand, revenue_90d,
    on_hand, days_of_supply, turnover_ratio, stock_status
)
SELECT
    product_id, product_name, category, sub_category,
    units_sold_90d,
    avg_daily_demand,
    revenue_90d,
    on_hand_raw::INT AS on_hand,
    CASE WHEN avg_daily_demand = 0 THEN NULL
         ELSE ROUND(on_hand_raw::NUMERIC / avg_daily_demand, 2)
    END AS days_of_supply,
    CASE WHEN on_hand_raw = 0 THEN NULL
         ELSE ROUND((units_sold_90d / 90.0 * 365) / NULLIF(on_hand_raw,0), 4)
    END AS turnover_ratio,
    CASE
        WHEN on_hand_raw = 0                                THEN 'OUT'
        WHEN avg_daily_demand > 0
             AND on_hand_raw / NULLIF(avg_daily_demand,0) < 7  THEN 'LOW'
        WHEN avg_daily_demand > 0
             AND on_hand_raw / NULLIF(avg_daily_demand,0) > 60 THEN 'OVERSTOCK'
        ELSE 'OK'
    END AS stock_status
FROM sim;
"""


def refresh_sales_daily() -> int:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(REFRESH_SALES_DAILY_SQL))
        n = conn.execute(text("SELECT COUNT(*) FROM marts.mart_sales_daily")).scalar_one()
    log.info("mart_sales_daily refreshed: %s rows", n)
    return n


def refresh_customer_360() -> int:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(REFRESH_CUSTOMER_360_SQL))
        n = conn.execute(text("SELECT COUNT(*) FROM marts.mart_customer_360")).scalar_one()
    log.info("mart_customer_360 refreshed: %s rows", n)
    return n


def refresh_inventory() -> int:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(REFRESH_INVENTORY_SQL))
        n = conn.execute(text("SELECT COUNT(*) FROM marts.mart_inventory")).scalar_one()
    log.info("mart_inventory refreshed: %s rows", n)
    return n


def refresh_all_marts() -> dict:
    return {
        "mart_sales_daily":    refresh_sales_daily(),
        "mart_customer_360":   refresh_customer_360(),
        "mart_inventory":      refresh_inventory(),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    print(refresh_all_marts())
