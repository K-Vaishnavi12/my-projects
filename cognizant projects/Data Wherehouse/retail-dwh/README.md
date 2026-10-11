# Retail Sales Data Warehouse & Analytics Platform

End-to-end data warehouse project built on a **100% free-tier** stack, showcasing dimensional modeling, ETL orchestration, SCD Type 2, data quality checks, and BI analytics.

> Built to demonstrate production-grade data engineering fundamentals — designed for Cognizant NPN / entry-level data engineering interviews.

---

## Business Problem

A retail chain needs a single source of truth for sales analytics. Raw transactional data lives in CSVs exported daily from the OLTP system. Analysts need:

- Daily sales KPIs (revenue, orders, AOV, discount %)
- Customer segmentation (RFM)
- Product performance & inventory turnover
- Historical tracking of customer address changes and product price changes (SCD2)

**Impact:** Reduced ad-hoc report generation from ~4 hours of manual Excel work to an 8-minute automated refresh.

---

## Architecture

```
+------------------+       +--------------+       +-------------------+       +----------------+       +------------+
| Source: CSV /    | ----> |   Staging    | ----> |   Core Warehouse  | ----> |   Data Marts   | ----> |  Power BI  |
| Superstore.csv   |       |  (raw layer) |       |   Star Schema     |       | (Sales/Cust)   |       | Dashboards |
+------------------+       +--------------+       +-------------------+       +----------------+       +------------+
        |                        |                        |                          |
        |                        |                        |                          |
        +---- Python Extract ----+---- Python Load -------+---- dbt Transform -------+
                                            |
                                            v
                              +-------------------------------+
                              |   Apache Airflow (Orchestr.)  |
                              |   retries, alerts, DQ checks  |
                              +-------------------------------+
```

**Layers**
1. **Raw / Staging** — 1:1 copy of the source CSV, all columns as TEXT, plus load metadata.
2. **Core (Star Schema)** — conformed dimensions + fact table, SCD Type 2 on `dim_customer` and `dim_product`.
3. **Marts** — pre-aggregated tables built via dbt for BI consumption.
4. **BI** — Power BI Desktop connected to Postgres via ODBC.

---

## Tech Stack (all free)

| Layer          | Tool                             |
| -------------- | -------------------------------- |
| Storage / DWH  | PostgreSQL 15 (Docker)           |
| Orchestration  | Apache Airflow 2.9 (Docker)      |
| ETL            | Python 3.11 (pandas, SQLAlchemy) |
| Transformation | dbt-core + dbt-postgres          |
| BI             | Power BI Desktop                 |
| Container      | Docker Compose                   |

---

## Data Model (Star Schema)

**Fact**
- `fact_sales` (order_id, order_line_id, date_key, product_key, customer_key, store_key, quantity, sales, discount, profit)

**Dimensions**
- `dim_customer` — **SCD Type 2** (tracks segment / region / city changes)
- `dim_product` — **SCD Type 2** (tracks category / price changes)
- `dim_date` — generated calendar dim (day/week/month/quarter/year/is_weekend/is_holiday)
- `dim_store` — region + state + city + postal code
- `dim_ship_mode` — small conformed dim

See `sql/ddl/` for full DDL.

---

## Project Structure

```
retail-dwh/
├── dags/                       # Airflow DAGs
│   └── retail_sales_etl_dag.py
├── etl/                        # Python ETL modules
│   ├── extract.py
│   ├── load_staging.py
│   ├── load_dim_scd2.py
│   ├── load_fact.py
│   ├── data_quality.py
│   └── utils/
│       └── db.py
├── sql/
│   ├── ddl/                    # CREATE TABLE scripts
│   │   ├── 01_schemas.sql
│   │   ├── 02_staging.sql
│   │   ├── 03_dimensions.sql
│   │   ├── 04_fact.sql
│   │   └── 05_dim_date_seed.sql
│   └── analytics/              # Business queries
│       ├── rfm_segmentation.sql
│       ├── sales_kpis.sql
│       └── top_products.sql
├── dbt/                        # dbt project
│   ├── dbt_project.yml
│   ├── profiles.yml.example
│   └── models/
│       ├── staging/
│       └── marts/
├── data/
│   ├── raw/                    # drop Superstore.csv here
│   └── processed/
├── docker/
│   └── docker-compose.yml
├── docs/
│   ├── architecture.png        # (add screenshot)
│   └── dashboard.png           # (add screenshot)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Quick Start

### 1. Prerequisites
- Docker Desktop
- Python 3.11+
- Power BI Desktop (Windows)
- Kaggle dataset: [Superstore Sales](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final) → save `Superstore.csv` to `data/raw/`

### 2. Bring up stack
```bash
cp .env.example .env
docker compose -f docker/docker-compose.yml up -d
```

Services:
- Postgres → `localhost:5432` (user: `retail`, db: `retail_dwh`)
- Airflow UI → `http://localhost:8081` (admin / admin)

### 3. Initialize warehouse
```bash
docker exec -i retail_postgres psql -U retail -d retail_dwh < sql/ddl/01_schemas.sql
docker exec -i retail_postgres psql -U retail -d retail_dwh < sql/ddl/02_staging.sql
docker exec -i retail_postgres psql -U retail -d retail_dwh < sql/ddl/03_dimensions.sql
docker exec -i retail_postgres psql -U retail -d retail_dwh < sql/ddl/04_fact.sql
docker exec -i retail_postgres psql -U retail -d retail_dwh < sql/ddl/05_dim_date_seed.sql
```

### 4. Trigger the DAG
Open Airflow UI → enable `retail_sales_etl` DAG → trigger a run.

### 5. Connect Power BI
Get Data → PostgreSQL → `localhost:5432` / `retail_dwh` → import fact + dim tables → build dashboards.

---

## Key Features (interview talking points)

- **Star schema** with conformed dimensions (why not snowflake? — fewer joins, faster BI queries)
- **SCD Type 2** on customer & product using `effective_from`, `effective_to`, `is_current`, `row_hash`
- **Incremental loading** using a `load_watermark` table (last successful `order_date`)
- **Data quality checks** — null keys, duplicate PKs, referential integrity, row-count reconciliation
- **Idempotent ETL** — safe to re-run; uses MERGE-style upserts
- **Partition-ready** — `fact_sales` includes `date_key` for future range partitioning
- **Orchestrated** — Airflow DAG with retries (3, exponential backoff), email on failure, task-level DQ gates

---

## Sample Interview Q&A

**Q: Star vs Snowflake schema?**
Star = denormalized dims, faster reads, simpler joins → best for BI. Snowflake = normalized dims, less redundancy, more joins → better when dims are huge and change often.

**Q: SCD Type 1 vs 2 vs 3?**
- Type 1 → overwrite (no history)
- Type 2 → new row per change with effective dates (full history) ← used here
- Type 3 → add "previous value" column (limited history)

**Q: How do you handle late-arriving facts?**
Look up dim surrogate key using `effective_from <= order_date < effective_to`; if dim row missing, insert a placeholder ("unknown member") and backfill later.

**Q: OLTP vs OLAP?**
OLTP = normalized (3NF), row-oriented, many small transactions. OLAP = denormalized (star), column-oriented friendly, few big analytical queries.

---

## Dashboards (Power BI)

1. **Sales Performance** — revenue trend, YoY %, top regions, discount vs profit
2. **Customer Segmentation** — RFM matrix, churn risk, CLV by segment
3. **Inventory & Product** — top/bottom SKUs, category mix, return rate

Screenshots in `docs/`.

---

## License
MIT
