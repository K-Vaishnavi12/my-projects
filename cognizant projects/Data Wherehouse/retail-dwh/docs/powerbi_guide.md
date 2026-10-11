# Power BI Dashboard Guide

## Connection
1. Power BI Desktop -> **Get Data** -> **PostgreSQL database**
2. Server: `localhost:5432`  Database: `retail_dwh`
3. Data Connectivity mode: **Import** (small dataset)
4. Load these tables from the `core` and `marts` schemas:
   - `core.fact_sales`
   - `core.dim_customer`
   - `core.dim_product`
   - `core.dim_date`
   - `core.dim_store`
   - `marts.mart_sales_daily`
   - `marts.mart_rfm`

## Relationships (Model view)
- `fact_sales[order_date_key]` -> `dim_date[date_key]`
- `fact_sales[customer_key]`   -> `dim_customer[customer_key]`
- `fact_sales[product_key]`    -> `dim_product[product_key]`
- `fact_sales[store_key]`      -> `dim_store[store_key]`

Filter direction: single (dim -> fact). Cardinality: many-to-one.

## Key DAX measures
```DAX
Revenue        = SUM(fact_sales[sales])
Profit         = SUM(fact_sales[profit])
Profit Margin  = DIVIDE([Profit], [Revenue])
Orders         = DISTINCTCOUNT(fact_sales[order_id])
AOV            = DIVIDE([Revenue], [Orders])
Revenue LY     = CALCULATE([Revenue], SAMEPERIODLASTYEAR(dim_date[full_date]))
Revenue YoY %  = DIVIDE([Revenue] - [Revenue LY], [Revenue LY])
```

## Suggested pages
1. **Sales Performance** — KPI cards (Revenue, Profit, Orders, AOV) + line chart (revenue over time) + map (by state) + bar (top categories).
2. **Customer Segmentation (RFM)** — scatter (Recency vs Monetary sized by Frequency), donut by segment, table of top customers.
3. **Product & Inventory** — treemap of category revenue, top 10 SKUs, discount vs profit scatter.
