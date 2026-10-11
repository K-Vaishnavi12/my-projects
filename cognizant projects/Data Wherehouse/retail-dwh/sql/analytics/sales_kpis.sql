-- =====================================================================
-- sales_kpis.sql : headline KPIs with YoY comparison using window fns
-- =====================================================================

WITH monthly AS (
    SELECT
        d.year,
        d.month,
        SUM(f.sales)   AS revenue,
        SUM(f.profit)  AS profit,
        COUNT(DISTINCT f.order_id) AS orders
    FROM core.fact_sales f
    JOIN core.dim_date   d ON d.date_key = f.order_date_key
    GROUP BY d.year, d.month
)
SELECT
    year, month, revenue, profit, orders,
    ROUND(profit / NULLIF(revenue,0), 4)                            AS profit_margin,
    LAG(revenue, 12) OVER (ORDER BY year, month)                    AS revenue_yoy_prev,
    ROUND(
        (revenue - LAG(revenue, 12) OVER (ORDER BY year, month))
        / NULLIF(LAG(revenue, 12) OVER (ORDER BY year, month), 0)
    , 4)                                                            AS revenue_yoy_pct
FROM monthly
ORDER BY year, month;
