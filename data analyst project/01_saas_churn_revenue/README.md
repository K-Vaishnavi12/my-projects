# SaaS Customer Churn & Revenue Retention

**Business problem:** Subscription churn impacting ARR.

## Data sources

- **Kaggle Telecom Churn** — [Telecom Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
- **Simulated SaaS subscription logs** — place in `data/` (see `data/README.md`)

## Tech stack

Python, SQL, Power BI, Pandas

## Key analysis

- Cohort retention analysis
- Churn probability segmentation
- SQL revenue lifetime analysis

## KPIs

| KPI | Description |
|-----|-------------|
| Monthly Churn Rate | % of customers who churned in the month |
| Customer Lifetime Value (LTV) | Expected revenue per customer over lifetime |
| Net Revenue Retention (NRR) | Revenue retained from existing customers (expansion/contraction) |

## Business impact

Simulated **22% churn reduction** improving **LTV by 18%**.

## Folder structure

- `data/` — raw and processed datasets
- `notebooks/` — exploratory and cohort analysis
- `scripts/` — reusable Python (cohort, churn model, ETL)
- `sql/` — revenue and lifetime value queries
- `power_bi/` — ARR dashboard design and measures
