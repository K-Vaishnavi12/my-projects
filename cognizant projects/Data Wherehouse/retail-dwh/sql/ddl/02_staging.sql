-- =====================================================================
-- 02_staging.sql : raw landing table (mirrors Superstore.csv columns)
-- All columns TEXT so bad data never breaks the load; casting happens
-- in the transform layer.
-- =====================================================================

DROP TABLE IF EXISTS staging.superstore_raw;

CREATE TABLE staging.superstore_raw (
    row_id         TEXT,
    order_id       TEXT,
    order_date     TEXT,
    ship_date      TEXT,
    ship_mode      TEXT,
    customer_id    TEXT,
    customer_name  TEXT,
    segment        TEXT,
    country        TEXT,
    city           TEXT,
    state          TEXT,
    postal_code    TEXT,
    region         TEXT,
    product_id     TEXT,
    category       TEXT,
    sub_category   TEXT,
    product_name   TEXT,
    sales          TEXT,
    quantity       TEXT,
    discount       TEXT,
    profit         TEXT,

    -- load metadata
    source_file    TEXT,
    loaded_at      TIMESTAMP DEFAULT NOW(),
    batch_id       TEXT
);

CREATE INDEX IF NOT EXISTS ix_staging_batch  ON staging.superstore_raw(batch_id);
CREATE INDEX IF NOT EXISTS ix_staging_order  ON staging.superstore_raw(order_id);
