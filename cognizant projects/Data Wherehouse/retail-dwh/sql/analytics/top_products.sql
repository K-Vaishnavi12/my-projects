-- =====================================================================
-- top_products.sql : top-10 products per category by revenue (window fn)
-- =====================================================================

WITH product_rev AS (
    SELECT
        dp.category,
        dp.sub_category,
        dp.product_name,
        SUM(f.sales)  AS revenue,
        SUM(f.profit) AS profit,
        SUM(f.quantity) AS units_sold
    FROM core.fact_sales f
    JOIN core.dim_product dp ON dp.product_key = f.product_key
    WHERE dp.is_current
    GROUP BY dp.category, dp.sub_category, dp.product_name
),
ranked AS (
    SELECT *,
        RANK() OVER (PARTITION BY category ORDER BY revenue DESC) AS rev_rank
    FROM product_rev
)
SELECT * FROM ranked
WHERE rev_rank <= 10
ORDER BY category, rev_rank;
