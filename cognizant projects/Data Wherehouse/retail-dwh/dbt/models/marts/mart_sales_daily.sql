-- Daily sales KPIs by region
{{ config(materialized='table') }}

SELECT
    d.full_date                                     AS order_date,
    ds.region,
    COUNT(DISTINCT f.order_id)                      AS orders,
    SUM(f.quantity)                                 AS units,
    SUM(f.sales)                                    AS revenue,
    SUM(f.profit)                                   AS profit,
    ROUND(SUM(f.profit) / NULLIF(SUM(f.sales),0), 4) AS profit_margin,
    ROUND(AVG(f.discount), 4)                       AS avg_discount,
    ROUND(SUM(f.sales) / NULLIF(COUNT(DISTINCT f.order_id),0), 2) AS avg_order_value
FROM {{ source('core', 'fact_sales') }} f
JOIN {{ source('core', 'dim_date')   }} d  ON d.date_key  = f.order_date_key
JOIN {{ source('core', 'dim_store')  }} ds ON ds.store_key = f.store_key
GROUP BY d.full_date, ds.region
