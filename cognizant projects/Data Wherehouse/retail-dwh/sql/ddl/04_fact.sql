-- =====================================================================
-- 04_fact.sql : fact_sales (grain = one row per order line)
-- Foreign keys reference SCD2 surrogate keys captured at load time.
-- =====================================================================

DROP TABLE IF EXISTS core.fact_sales CASCADE;

CREATE TABLE core.fact_sales (
    sales_key       BIGSERIAL PRIMARY KEY,

    -- degenerate dimensions
    order_id        TEXT     NOT NULL,
    row_id          INTEGER,

    -- foreign keys to dims (surrogate keys resolved at load time)
    order_date_key  INTEGER  NOT NULL REFERENCES core.dim_date(date_key),
    ship_date_key   INTEGER           REFERENCES core.dim_date(date_key),
    customer_key    BIGINT   NOT NULL REFERENCES core.dim_customer(customer_key),
    product_key     BIGINT   NOT NULL REFERENCES core.dim_product(product_key),
    store_key       INTEGER  NOT NULL REFERENCES core.dim_store(store_key),
    ship_mode_key   INTEGER  NOT NULL REFERENCES core.dim_ship_mode(ship_mode_key),

    -- measures (additive except discount)
    quantity        INTEGER       NOT NULL,
    sales           NUMERIC(14,2) NOT NULL,
    discount        NUMERIC(6,4)  NOT NULL DEFAULT 0,
    profit          NUMERIC(14,2) NOT NULL DEFAULT 0,

    -- audit
    batch_id        TEXT,
    loaded_at       TIMESTAMP DEFAULT NOW()
);

-- Indexes for typical BI query patterns
CREATE INDEX ix_fact_sales_order_date  ON core.fact_sales(order_date_key);
CREATE INDEX ix_fact_sales_customer    ON core.fact_sales(customer_key);
CREATE INDEX ix_fact_sales_product     ON core.fact_sales(product_key);
CREATE INDEX ix_fact_sales_store       ON core.fact_sales(store_key);
CREATE INDEX ix_fact_sales_order_id    ON core.fact_sales(order_id);

-- Natural-key uniqueness (idempotent loads)
CREATE UNIQUE INDEX ux_fact_sales_natural
    ON core.fact_sales(order_id, product_key, row_id);
