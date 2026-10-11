-- =====================================================================
-- 03_dimensions.sql : conformed dimensions
-- SCD Type 2 on dim_customer and dim_product.
-- Type 1 on small/static dims (store, ship_mode, date).
-- =====================================================================

-- ---------------------------------------------------------------------
-- dim_date : one row per calendar day (seeded separately)
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS core.dim_date CASCADE;
CREATE TABLE core.dim_date (
    date_key       INTEGER PRIMARY KEY,   -- YYYYMMDD
    full_date      DATE    NOT NULL UNIQUE,
    day            SMALLINT,
    day_name       TEXT,
    day_of_week    SMALLINT,
    week           SMALLINT,
    month          SMALLINT,
    month_name     TEXT,
    quarter        SMALLINT,
    year           SMALLINT,
    is_weekend     BOOLEAN,
    is_month_end   BOOLEAN
);

-- ---------------------------------------------------------------------
-- dim_ship_mode : small Type-1 dim
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS core.dim_ship_mode CASCADE;
CREATE TABLE core.dim_ship_mode (
    ship_mode_key  SERIAL PRIMARY KEY,
    ship_mode      TEXT NOT NULL UNIQUE
);

-- ---------------------------------------------------------------------
-- dim_store : geography (Type 1)
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS core.dim_store CASCADE;
CREATE TABLE core.dim_store (
    store_key      SERIAL PRIMARY KEY,
    country        TEXT,
    region         TEXT,
    state          TEXT,
    city           TEXT,
    postal_code    TEXT,
    UNIQUE (country, region, state, city, postal_code)
);

-- ---------------------------------------------------------------------
-- dim_customer : SCD Type 2
--   business key  = customer_id
--   surrogate key = customer_key (used by fact)
--   tracks name + segment (geography lives in dim_store; a Superstore
--   customer can ship to multiple addresses so geo is not customer-stable)
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS core.dim_customer CASCADE;
CREATE TABLE core.dim_customer (
    customer_key    BIGSERIAL PRIMARY KEY,
    customer_id     TEXT      NOT NULL,   -- business key
    customer_name   TEXT,
    segment         TEXT,

    -- SCD2 tracking
    row_hash        TEXT      NOT NULL,
    effective_from  TIMESTAMP NOT NULL DEFAULT NOW(),
    effective_to    TIMESTAMP NOT NULL DEFAULT '9999-12-31'::TIMESTAMP,
    is_current      BOOLEAN   NOT NULL DEFAULT TRUE,
    version         INTEGER   NOT NULL DEFAULT 1
);
CREATE INDEX ix_dim_customer_bk       ON core.dim_customer(customer_id);
CREATE INDEX ix_dim_customer_current  ON core.dim_customer(customer_id) WHERE is_current;

-- ---------------------------------------------------------------------
-- dim_product : SCD Type 2
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS core.dim_product CASCADE;
CREATE TABLE core.dim_product (
    product_key     BIGSERIAL PRIMARY KEY,
    product_id      TEXT      NOT NULL,   -- business key
    product_name    TEXT,
    category        TEXT,
    sub_category    TEXT,

    row_hash        TEXT      NOT NULL,
    effective_from  TIMESTAMP NOT NULL DEFAULT NOW(),
    effective_to    TIMESTAMP NOT NULL DEFAULT '9999-12-31'::TIMESTAMP,
    is_current      BOOLEAN   NOT NULL DEFAULT TRUE,
    version         INTEGER   NOT NULL DEFAULT 1
);
CREATE INDEX ix_dim_product_bk       ON core.dim_product(product_id);
CREATE INDEX ix_dim_product_current  ON core.dim_product(product_id) WHERE is_current;
