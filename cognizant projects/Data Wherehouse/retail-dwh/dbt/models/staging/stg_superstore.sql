-- Cleaned view over the staging table (typed, deduped)
{{ config(materialized='view') }}

WITH src AS (
    SELECT
        row_id::INT                              AS row_id,
        order_id,
        order_date::DATE                         AS order_date,
        ship_date::DATE                          AS ship_date,
        ship_mode,
        customer_id,
        product_id,
        quantity::INT                            AS quantity,
        sales::NUMERIC(14,2)                     AS sales,
        discount::NUMERIC(6,4)                   AS discount,
        profit::NUMERIC(14,2)                    AS profit,
        batch_id
    FROM {{ source('staging', 'superstore_raw') }}
)
SELECT * FROM src
