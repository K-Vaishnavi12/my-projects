-- =====================================================================
-- rfm_segmentation.sql : plain SQL version (no dbt required)
-- =====================================================================

WITH base AS (
    SELECT
        dc.customer_id,
        MAX(d.full_date)             AS last_order_date,
        COUNT(DISTINCT f.order_id)   AS frequency,
        SUM(f.sales)                 AS monetary
    FROM core.fact_sales   f
    JOIN core.dim_customer dc ON dc.customer_key = f.customer_key AND dc.is_current
    JOIN core.dim_date     d  ON d.date_key      = f.order_date_key
    GROUP BY dc.customer_id
),
scored AS (
    SELECT
        customer_id,
        (CURRENT_DATE - last_order_date) AS recency_days,
        frequency,
        monetary,
        NTILE(5) OVER (ORDER BY (CURRENT_DATE - last_order_date) DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency) AS f_score,
        NTILE(5) OVER (ORDER BY monetary)  AS m_score
    FROM base
)
SELECT
    customer_id,
    recency_days, frequency, monetary,
    r_score, f_score, m_score,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 4 AND f_score >= 3                  THEN 'Loyal'
        WHEN r_score >= 4                                   THEN 'New / Promising'
        WHEN r_score <= 2 AND f_score >= 4                  THEN 'At Risk'
        WHEN r_score <= 2 AND m_score >= 4                  THEN 'Cant Lose Them'
        WHEN r_score <= 2                                   THEN 'Hibernating'
        ELSE 'Needs Attention'
    END AS segment
FROM scored
ORDER BY monetary DESC;
