-- =====================================================================
-- 05_dim_date_seed.sql : populate dim_date for 2010-01-01 to 2035-12-31
-- =====================================================================

TRUNCATE TABLE core.dim_date CASCADE;

INSERT INTO core.dim_date (
    date_key, full_date, day, day_name, day_of_week,
    week, month, month_name, quarter, year,
    is_weekend, is_month_end
)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INT                              AS date_key,
    d::DATE                                                  AS full_date,
    EXTRACT(DAY   FROM d)::SMALLINT                          AS day,
    TO_CHAR(d, 'Day')                                        AS day_name,
    EXTRACT(ISODOW FROM d)::SMALLINT                         AS day_of_week,
    EXTRACT(WEEK  FROM d)::SMALLINT                          AS week,
    EXTRACT(MONTH FROM d)::SMALLINT                          AS month,
    TO_CHAR(d, 'Month')                                      AS month_name,
    EXTRACT(QUARTER FROM d)::SMALLINT                        AS quarter,
    EXTRACT(YEAR  FROM d)::SMALLINT                          AS year,
    EXTRACT(ISODOW FROM d) IN (6,7)                          AS is_weekend,
    (d = (DATE_TRUNC('month', d) + INTERVAL '1 month - 1 day')) AS is_month_end
FROM generate_series('2010-01-01'::DATE, '2035-12-31'::DATE, INTERVAL '1 day') AS d;

-- Seed static ship_mode values (Superstore has 4)
INSERT INTO core.dim_ship_mode (ship_mode) VALUES
    ('Standard Class'),
    ('Second Class'),
    ('First Class'),
    ('Same Day')
ON CONFLICT (ship_mode) DO NOTHING;
