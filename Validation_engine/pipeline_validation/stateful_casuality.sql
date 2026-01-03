-- CHECK A: The "Impossible Order" (Stateful Ghost)
CREATE OR REPLACE VIEW validation.violation_causal_impossible_orders AS
WITH marketing_memory AS (
    SELECT 
        date_id,
        channel,

        SUM(spend) OVER (
            PARTITION BY channel 
            ORDER BY date_id 
            ROWS BETWEEN 30 PRECEDING AND CURRENT ROW
        ) as adstock_pool
    FROM validation.snap_fact_marketing
),
daily_orders AS (
    SELECT 
        date_id, 
        marketing_channel, 
        COUNT(order_id) as order_count,
        SUM(price) as revenue_at_risk 
    FROM validation.snap_fact_orders
    WHERE marketing_channel NOT IN ('Direct/Organic', 'Organic_SEO')
    GROUP BY 1, 2
)
SELECT 
    o.date_id,
    o.marketing_channel,
    o.order_count,
    o.revenue_at_risk,
    COALESCE(m.adstock_pool, 0) as historical_spend_pool
FROM daily_orders o
LEFT JOIN marketing_memory m 
    ON o.date_id = m.date_id 
    AND o.marketing_channel = m.channel
WHERE 
    COALESCE(m.adstock_pool, 0) = 0;

-- CHECK B: Temporal Causality (Future Leakage)
CREATE OR REPLACE VIEW validation.violation_temporal_future_leakage AS
SELECT 
    o.order_id,
    o.date_id as order_date,
    o.marketing_channel,
    MIN(m.date_id) as first_channel_activity_date
FROM validation.snap_fact_orders o
JOIN validation.snap_fact_marketing m 
    ON o.marketing_channel = m.channel
WHERE 
    o.marketing_channel NOT IN ('Direct/Organic', 'Organic_SEO')
GROUP BY 1, 2, 3
HAVING o.date_id < MIN(m.date_id);