/*
================================================================================
Advanced Data Analytics Queries
Author: Data Analyst Portfolio
Description: Simulates complex SQL data extraction for the React Dashboard. 
Demonstrates mastery of CTEs, Window Functions, and Date Arithmetic.
================================================================================
*/

-- 1. Net Revenue Retention (NRR) and Churn Calculation
-- Simulates the data pulling process for the main Churn & Revenue KPIs
WITH MonthlyRevenue AS (
    SELECT 
        customer_id,
        DATE_TRUNC('month', billing_date) AS billing_month,
        SUM(amount) AS mrr
    FROM 
        subscriptions
    GROUP BY 
        customer_id, DATE_TRUNC('month', billing_date)
),
RevenueChanges AS (
    SELECT 
        curr.customer_id,
        curr.billing_month,
        curr.mrr AS current_mrr,
        COALESCE(prev.mrr, 0) AS previous_mrr,
        CASE 
            WHEN prev.mrr IS NULL THEN 'New'
            WHEN curr.mrr > prev.mrr THEN 'Expansion'
            WHEN curr.mrr < prev.mrr THEN 'Contraction'
            ELSE 'Retained'
        END AS revenue_type
    FROM 
        MonthlyRevenue curr
    LEFT JOIN 
        MonthlyRevenue prev ON curr.customer_id = prev.customer_id 
        AND curr.billing_month = prev.billing_month + INTERVAL '1 month'
),
ChurnedRevenue AS (
    SELECT 
        prev.customer_id,
        prev.billing_month + INTERVAL '1 month' AS billing_month,
        0 AS current_mrr,
        prev.mrr AS previous_mrr,
        'Churn' AS revenue_type
    FROM 
        MonthlyRevenue prev
    LEFT JOIN 
        MonthlyRevenue curr ON curr.customer_id = prev.customer_id 
        AND curr.billing_month = prev.billing_month + INTERVAL '1 month'
    WHERE 
        curr.customer_id IS NULL
)
SELECT 
    billing_month,
    SUM(CASE WHEN revenue_type = 'New' THEN current_mrr ELSE 0 END) AS new_mrr,
    SUM(CASE WHEN revenue_type = 'Expansion' THEN current_mrr - previous_mrr ELSE 0 END) AS expansion_mrr,
    SUM(CASE WHEN revenue_type = 'Contraction' THEN previous_mrr - current_mrr ELSE 0 END) AS contraction_mrr,
    SUM(CASE WHEN revenue_type = 'Churn' THEN previous_mrr ELSE 0 END) AS churned_mrr,
    SUM(CASE WHEN revenue_type != 'Churn' THEN current_mrr ELSE 0 END) AS total_mrr
FROM 
    (SELECT * FROM RevenueChanges UNION ALL SELECT * FROM ChurnedRevenue) combined
GROUP BY 
    billing_month
ORDER BY 
    billing_month DESC;


-- 2. Cohort Retention Analysis (Heatmap Data Source)
-- Determines user retention % by cohort month (e.g., Month 0, Month 1...)
WITH CohortDefinition AS (
    SELECT 
        customer_id,
        DATE_TRUNC('month', MIN(subscription_start_date)) AS cohort_month
    FROM 
        subscriptions
    GROUP BY 
        customer_id
),
ActiveMonths AS (
    SELECT 
        s.customer_id,
        DATE_TRUNC('month', s.billing_date) AS active_month,
        c.cohort_month,
        EXTRACT(EPOCH FROM (DATE_TRUNC('month', s.billing_date) - c.cohort_month)) / 2592000 AS months_since_start -- Approximate month diff
    FROM 
        subscriptions s
    JOIN 
        CohortDefinition c ON s.customer_id = c.customer_id
),
CohortCounts AS (
    SELECT 
        cohort_month,
        COUNT(DISTINCT customer_id) AS original_size
    FROM 
        CohortDefinition
    GROUP BY 
        cohort_month
)
SELECT 
    am.cohort_month,
    am.months_since_start,
    COUNT(DISTINCT am.customer_id) AS retained_users,
    cc.original_size,
    ROUND((COUNT(DISTINCT am.customer_id)::NUMERIC / cc.original_size) * 100, 2) AS retention_percentage
FROM 
    ActiveMonths am
JOIN 
    CohortCounts cc ON am.cohort_month = cc.cohort_month
GROUP BY 
    am.cohort_month, am.months_since_start, cc.original_size
ORDER BY 
    am.cohort_month, am.months_since_start;


-- 3. A/B Testing Statistical Aggregation
-- Aggregates raw event logs into control/variant buckets for statistical testing
SELECT 
    experiment_variant,
    COUNT(DISTINCT session_id) AS total_sessions,
    COUNT(DISTINCT CASE WHEN converted = TRUE THEN session_id ELSE NULL END) AS total_conversions,
    ROUND((COUNT(DISTINCT CASE WHEN converted = TRUE THEN session_id ELSE NULL END)::NUMERIC / COUNT(DISTINCT session_id)) * 100, 2) AS conversion_rate,
    SUM(revenue_generated) AS total_revenue
FROM 
    page_events
WHERE 
    experiment_id = 'EXP-2023-NEW-CHECKOUT'
    AND event_timestamp >= '2023-11-01'
GROUP BY 
    experiment_variant;
