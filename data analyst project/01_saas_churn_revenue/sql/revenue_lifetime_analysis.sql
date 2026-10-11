-- Revenue & Lifetime Value Analysis (SaaS subscriptions)
-- Use with subscriptions (subscription_id, customer_id, plan_id, mrr, start_date, end_date, status)
-- and customers (customer_id, signup_date, segment, region)

-- Monthly recurring revenue (MRR) by month
WITH mrr_by_month AS (
    SELECT
        DATE_TRUNC('month', start_date) AS month,
        SUM(mrr) AS mrr,
        COUNT(DISTINCT customer_id) AS active_customers
    FROM subscriptions
    WHERE (end_date IS NULL OR end_date >= DATE_TRUNC('month', CURRENT_DATE))
      AND start_date <= DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
    GROUP BY 1
)
SELECT * FROM mrr_by_month ORDER BY month;

-- Customer Lifetime Value (LTV): total revenue per customer over their lifetime
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(mrr * EXTRACT(MONTH FROM AGE(COALESCE(end_date, CURRENT_DATE), start_date))) AS total_revenue
    FROM subscriptions
    GROUP BY customer_id
)
SELECT
    customer_id,
    total_revenue AS lifetime_revenue,
    ROUND(total_revenue / NULLIF(COUNT(*) OVER (), 0), 2) AS avg_ltv
FROM customer_revenue;

-- Monthly churn rate (customers who ended in month / active at start of month)
WITH cohort_active AS (
    SELECT
        DATE_TRUNC('month', start_date) AS cohort_month,
        customer_id
    FROM subscriptions
    WHERE end_date IS NULL OR end_date >= CURRENT_DATE
),
churned_in_month AS (
    SELECT
        DATE_TRUNC('month', end_date) AS churn_month,
        COUNT(DISTINCT customer_id) AS churned_count
    FROM subscriptions
    WHERE end_date IS NOT NULL
    GROUP BY 1
)
SELECT
    c.churn_month AS month,
    c.churned_count,
    ca.active_customers,
    ROUND(100.0 * c.churned_count / NULLIF(ca.active_customers, 0), 2) AS churn_rate_pct
FROM churned_in_month c
LEFT JOIN (
    SELECT DATE_TRUNC('month', cohort_month) AS m, COUNT(DISTINCT customer_id) AS active_customers
    FROM cohort_active
    GROUP BY 1
) ca ON ca.m = c.churn_month
ORDER BY month;

-- Net Revenue Retention (simplified): compare cohort MRR at T0 vs current MRR from same cohort
WITH cohort_mrr AS (
    SELECT
        DATE_TRUNC('month', MIN(s.start_date)) AS cohort_month,
        s.customer_id,
        SUM(s.mrr) AS mrr
    FROM subscriptions s
    GROUP BY s.customer_id
),
current_mrr AS (
    SELECT customer_id, SUM(mrr) AS mrr
    FROM subscriptions
    WHERE end_date IS NULL OR end_date >= CURRENT_DATE
    GROUP BY customer_id
)
SELECT
    cm.cohort_month,
    SUM(cm.mrr) AS beginning_mrr,
    SUM(COALESCE(cr.mrr, 0)) AS current_mrr,
    ROUND(100.0 * SUM(COALESCE(cr.mrr, 0)) / NULLIF(SUM(cm.mrr), 0), 2) AS nrr_pct
FROM cohort_mrr cm
LEFT JOIN current_mrr cr ON cm.customer_id = cr.customer_id
GROUP BY cm.cohort_month
ORDER BY cm.cohort_month;
