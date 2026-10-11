-- =====================================================================
-- 06_returns.sql : second data source - product returns
-- Adds a staging table + fact_returns sharing conformed dims with fact_sales.
-- Two facts sharing dimensions = textbook Kimball "fact constellation".
-- =====================================================================

DROP TABLE IF EXISTS staging.returns_raw;

CREATE TABLE staging.returns_raw (
    return_id          TEXT,
    order_id           TEXT,
    row_id             TEXT,
    product_id         TEXT,
    customer_id        TEXT,
    return_date        TEXT,
    reason             TEXT,
    refund_amount      TEXT,
    quantity_returned  TEXT,
    batch_id           TEXT,
    loaded_at          TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_stg_returns_batch ON staging.returns_raw(batch_id);


DROP TABLE IF EXISTS core.fact_returns CASCADE;

CREATE TABLE core.fact_returns (
    return_key         BIGSERIAL PRIMARY KEY,

    -- degenerate dim (business key)
    return_id          TEXT NOT NULL UNIQUE,
    order_id           TEXT NOT NULL,
    row_id             INTEGER,

    -- foreign keys to conformed dims
    return_date_key    INTEGER NOT NULL REFERENCES core.dim_date(date_key),
    order_date_key     INTEGER NOT NULL REFERENCES core.dim_date(date_key),
    customer_key       BIGINT  NOT NULL REFERENCES core.dim_customer(customer_key),
    product_key        BIGINT  NOT NULL REFERENCES core.dim_product(product_key),

    -- measures
    quantity_returned  INTEGER      NOT NULL,
    refund_amount      NUMERIC(14,2) NOT NULL,
    reason             TEXT,

    -- audit
    batch_id           TEXT,
    loaded_at          TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ix_fact_returns_order      ON core.fact_returns(order_id);
CREATE INDEX ix_fact_returns_customer   ON core.fact_returns(customer_key);
CREATE INDEX ix_fact_returns_product    ON core.fact_returns(product_key);
CREATE INDEX ix_fact_returns_ret_date   ON core.fact_returns(return_date_key);
