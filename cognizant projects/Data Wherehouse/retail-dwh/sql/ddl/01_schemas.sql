-- =====================================================================
-- 01_schemas.sql : create logical schemas / layers
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS staging;   -- raw 1:1 copy of source
CREATE SCHEMA IF NOT EXISTS core;      -- star schema (facts + dims)
CREATE SCHEMA IF NOT EXISTS marts;     -- pre-aggregated marts for BI
CREATE SCHEMA IF NOT EXISTS meta;      -- ETL metadata (watermarks, DQ logs)

-- ETL watermark for incremental loads
CREATE TABLE IF NOT EXISTS meta.load_watermark (
    table_name       TEXT PRIMARY KEY,
    last_loaded_at   TIMESTAMP NOT NULL,
    last_order_date  DATE
);

-- ETL run log
CREATE TABLE IF NOT EXISTS meta.etl_run_log (
    run_id       BIGSERIAL PRIMARY KEY,
    dag_run_id   TEXT,
    task_id      TEXT,
    status       TEXT,          -- SUCCESS / FAILED
    rows_read    BIGINT,
    rows_written BIGINT,
    message      TEXT,
    started_at   TIMESTAMP DEFAULT NOW(),
    ended_at     TIMESTAMP
);

-- Data-quality check log
CREATE TABLE IF NOT EXISTS meta.dq_check_log (
    check_id    BIGSERIAL PRIMARY KEY,
    run_id      BIGINT,
    check_name  TEXT NOT NULL,
    table_name  TEXT NOT NULL,
    status      TEXT NOT NULL,  -- PASS / FAIL
    failed_rows BIGINT,
    details     TEXT,
    checked_at  TIMESTAMP DEFAULT NOW()
);
