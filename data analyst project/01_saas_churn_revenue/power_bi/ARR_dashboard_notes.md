# ARR Tracking Dashboard — Design Notes

## Purpose
Single view for revenue retention: ARR, churn, NRR, and cohort health.

## Key visuals

1. **ARR trend** — Line chart: ARR by month (from MRR × 12 or summed annual contracts).
2. **Monthly churn rate** — Card or line: Churn % (churned customers / beginning-of-month active).
3. **Net Revenue Retention** — Card or trend: NRR % by cohort or overall.
4. **Cohort retention heatmap** — Matrix: cohort (rows) × period (columns), value = retention %.
5. **LTV by segment** — Bar chart: average LTV by segment (SMB, Mid-Market, Enterprise).
6. **At-risk pipeline** — Table: high churn-probability accounts (from model output).

## Measures (DAX ideas)

- **ARR** = SUM(subscriptions[mrr]) * 12 (for active only), or use pre-aggregated ARR table.
- **Churn Rate** = DIVIDE(Churned Count, Beginning Period Customers, 0).
- **NRR** = DIVIDE(Current Cohort MRR, Beginning Cohort MRR, 0).

## Data model
- `Subscriptions` (fact): subscription_id, customer_id, mrr, start_date, end_date, status.
- `Customers` (dim): customer_id, signup_date, segment, region.
- Optional: `CohortRetention` table from Python export for heatmap.

## Export from Python
Scripts in `../scripts/` can output:
- `cohort_retention_matrix.csv` for heatmap.
- `churn_risk_segments.csv` for at-risk list.
- Monthly KPI table for ARR and churn rate time series.
