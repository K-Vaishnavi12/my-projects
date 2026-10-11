-- =====================================================================
-- 07_marts.sql : pre-aggregated marts for BI
-- These are materialised tables refreshed by the ETL after fact loads.
-- =====================================================================

-- ---------------------------------------------------------------------
-- marts.mart_sales_daily : one row per (region, day) - built by Python
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS marts.mart_sales_daily;
CREATE TABLE marts.mart_sales_daily (
    order_date       DATE,
    region           TEXT,
    orders           INTEGER,
    units            INTEGER,
    revenue          NUMERIC(14,2),
    profit           NUMERIC(14,2),
    profit_margin    NUMERIC(6,4),
    avg_discount     NUMERIC(6,4),
    avg_order_value  NUMERIC(14,2),
    refreshed_at     TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (order_date, region)
);
CREATE INDEX ix_mart_sales_daily_date ON marts.mart_sales_daily(order_date);

-- ---------------------------------------------------------------------
-- marts.mart_customer_360 : single view of customer
-- Combines fact_sales, fact_returns, and RFM scores.
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS marts.mart_customer_360;
CREATE TABLE marts.mart_customer_360 (
    customer_id        TEXT PRIMARY KEY,
    customer_name      TEXT,
    segment            TEXT,

    -- lifetime purchase behaviour
    first_order_date   DATE,
    last_order_date    DATE,
    total_orders       INTEGER,
    total_units        INTEGER,
    lifetime_revenue   NUMERIC(14,2),
    lifetime_profit    NUMERIC(14,2),
    avg_order_value    NUMERIC(14,2),

    -- returns behaviour
    total_returns      INTEGER,
    total_refunded     NUMERIC(14,2),
    return_rate        NUMERIC(6,4),      -- returns / orders

    -- RFM
    recency_days       INTEGER,
    frequency          INTEGER,
    monetary           NUMERIC(14,2),
    r_score            SMALLINT,
    f_score            SMALLINT,
    m_score            SMALLINT,
    rfm_segment        TEXT,

    refreshed_at       TIMESTAMP DEFAULT NOW()
);
CREATE INDEX ix_c360_segment ON marts.mart_customer_360(rfm_segment);

-- ---------------------------------------------------------------------
-- marts.mart_inventory : per-product supply and turnover metrics
-- Grain: one row per product.
-- Note: Superstore has no true stock feed, so on_hand is simulated as
--   90-day-average-demand * random(1..4) - this is realistic enough
--   to demonstrate inventory KPIs (days-of-supply, turnover ratio).
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS marts.mart_inventory;
CREATE TABLE marts.mart_inventory (
    product_id            TEXT PRIMARY KEY,
    product_name          TEXT,
    category              TEXT,
    sub_category          TEXT,

    units_sold_90d        INTEGER,
    avg_daily_demand      NUMERIC(10,2),
    revenue_90d           NUMERIC(14,2),

    on_hand               INTEGER,          -- simulated
    days_of_supply        NUMERIC(10,2),    -- on_hand / avg_daily_demand
    turnover_ratio        NUMERIC(10,4),    -- annualised

    stock_status          TEXT,             -- OUT / LOW / OK / OVERSTOCK

    refreshed_at          TIMESTAMP DEFAULT NOW()
);
CREATE INDEX ix_inventory_status ON marts.mart_inventory(stock_status);
