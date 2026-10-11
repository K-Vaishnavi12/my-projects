-- Ad Spend & Attribution — SQL snippets
-- Tables: campaign_spend (date, channel, spend, impressions, clicks)
--         conversions (conversion_id, user_id, conversion_date, conversion_value, conversion_type)

-- Spend by channel (monthly)
SELECT
    DATE_TRUNC('month', date) AS month,
    channel,
    SUM(spend) AS spend,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks
FROM campaign_spend
GROUP BY 1, 2
ORDER BY 1, 2;

-- CAC by channel (spend / new customers in same period)
WITH new_customers AS (
    SELECT
        DATE_TRUNC('month', conversion_date) AS month,
        channel_attributed AS channel,  -- from attribution model export
        COUNT(DISTINCT user_id) AS new_customers
    FROM conversions c
    LEFT JOIN attribution_by_conversion a ON c.conversion_id = a.conversion_id
    WHERE conversion_type IN ('trial', 'paid')
    GROUP BY 1, 2
),
spend_by_channel AS (
    SELECT
        DATE_TRUNC('month', date) AS month,
        channel,
        SUM(spend) AS spend
    FROM campaign_spend
    GROUP BY 1, 2
)
SELECT
    s.month,
    s.channel,
    s.spend,
    COALESCE(n.new_customers, 0) AS new_customers,
    ROUND(s.spend / NULLIF(n.new_customers, 0), 2) AS cac
FROM spend_by_channel s
LEFT JOIN new_customers n ON s.month = n.month AND s.channel = n.channel
ORDER BY 1, 2;

-- ROAS by channel (revenue from conversions / spend)
WITH revenue_by_channel AS (
    SELECT
        DATE_TRUNC('month', c.conversion_date) AS month,
        a.channel,
        SUM(c.conversion_value) AS revenue
    FROM conversions c
    JOIN attribution_by_conversion a ON c.conversion_id = a.conversion_id
    GROUP BY 1, 2
)
SELECT
    r.month,
    r.channel,
    r.revenue,
    s.spend,
    ROUND(r.revenue / NULLIF(s.spend, 0), 2) AS roas
FROM revenue_by_channel r
JOIN (
    SELECT DATE_TRUNC('month', date) AS month, channel, SUM(spend) AS spend
    FROM campaign_spend
    GROUP BY 1, 2
) s ON r.month = s.month AND r.channel = s.channel
ORDER BY 1, 2;
