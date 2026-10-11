-- ============================================================
-- 02_seed.sql : idempotent seed data
-- ============================================================
-- Seed topic buckets so dashboards work even before the first ETL.
-- Personas are seeded from Python (registry), NOT here, to avoid
-- drift between code and DB.
-- ============================================================

INSERT OR IGNORE INTO dim_topic(topic_key) VALUES
    ('history'),
    ('science'),
    ('philosophy'),
    ('literature'),
    ('current_events');
