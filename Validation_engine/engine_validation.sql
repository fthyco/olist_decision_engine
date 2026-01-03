-- =========================================================
-- LAYER 2: PHYSICS & DYNAMICS VERIFICATION
-- =========================================================
-- 1. CONSERVATION OF DEMAND (The Funnel Ceiling)
CREATE OR REPLACE VIEW validation.violation_physics_demand_overflow AS
WITH daily_traffic AS (
    SELECT 
        date_id, 
        channel, 
        SUM(clicks) as traffic_in
    FROM validation.snap_fact_marketing
    GROUP BY 1, 2
),
daily_conversions AS (
    SELECT 
        date_id, 
        marketing_channel, 
        COUNT(order_id) as conversions_out
    FROM validation.snap_fact_financials
    GROUP BY 1, 2
)
SELECT 
    t.date_id,
    t.channel,
    t.traffic_in,
    c.conversions_out,
    (c.conversions_out::decimal / NULLIF(t.traffic_in, 0)) as conversion_rate
FROM daily_traffic t
JOIN daily_conversions c 
    ON t.date_id = c.date_id 
    AND t.channel = c.marketing_channel
WHERE 
    c.conversions_out > t.traffic_in 
    OR 
    (c.conversions_out::decimal / NULLIF(t.traffic_in, 0)) > 0.40; 

-- 2. CHANNEL SATURATION SANITY (Diminishing Returns)

CREATE OR REPLACE VIEW validation.violation_physics_infinite_scaling AS
WITH metrics AS (
    SELECT 
        date_id,
        channel,
        spend,
        clicks,
        LAG(spend) OVER (PARTITION BY channel ORDER BY date_id) as prev_spend,
        LAG(clicks) OVER (PARTITION BY channel ORDER BY date_id) as prev_clicks
    FROM validation.snap_fact_marketing
    WHERE spend > 500 
)
SELECT 
    *,
    (spend - prev_spend) as delta_spend,
    (clicks - prev_clicks) as delta_clicks
FROM metrics
WHERE 
    spend > (prev_spend * 1.5) 
    AND 
    (clicks - prev_clicks) > (prev_clicks * 1.5) 
    AND channel NOT IN ('Email'); 

-- 3. CROSS-CHANNEL LEAKAGE (Share of Voice vs. Share of Attribution)
CREATE OR REPLACE VIEW validation.violation_physics_attribution_skew AS
WITH total_daily AS (
    SELECT date_id, SUM(spend) as total_spend, SUM(clicks) as total_clicks FROM validation.snap_fact_marketing GROUP BY 1
),
channel_share AS (
    SELECT 
        m.date_id,
        m.channel,
        (m.spend / NULLIF(t.total_spend, 1)) as share_of_spend,
        (m.clicks / NULLIF(t.total_clicks, 1)) as share_of_clicks
    FROM validation.snap_fact_marketing m
    JOIN total_daily t ON m.date_id = t.date_id
),
attribution_share AS (
    SELECT 
        f.date_id,
        f.marketing_channel,
        COUNT(*) / NULLIF(SUM(COUNT(*)) OVER (PARTITION BY f.date_id), 1)::decimal as share_of_orders
    FROM validation.snap_fact_financials f
    WHERE f.marketing_channel NOT IN ('Direct/Organic', 'Unknown')
    GROUP BY 1, 2
)
SELECT 
    s.date_id,
    s.channel,
    ROUND(s.share_of_spend, 2) as spend_share,
    ROUND(a.share_of_orders, 2) as order_share,
    (a.share_of_orders - s.share_of_spend) as leverage_delta
FROM channel_share s
JOIN attribution_share a 
    ON s.date_id = a.date_id 
    AND s.channel = a.marketing_channel
WHERE 
    (a.share_of_orders - s.share_of_spend) > 0.50; 

-- 4. ORDER-LEVEL MASS BALANCE (Rolling Window Conservation)

CREATE OR REPLACE VIEW validation.violation_physics_rolling_mass_balance AS
WITH daily_bal AS (
    SELECT 
        COALESCE(m.date_id, f.date_id) as date_id,
        (COALESCE(m.spend, 0) - COALESCE(f.cac, 0)) as daily_diff
    FROM (SELECT date_id, SUM(spend) as spend FROM validation.snap_fact_marketing GROUP BY 1) m
    FULL OUTER JOIN (SELECT date_id, SUM(acquisition_cost) as cac FROM validation.snap_fact_financials GROUP BY 1) f
    ON m.date_id = f.date_id
)
SELECT 
    date_id,
    daily_diff,
    SUM(daily_diff) OVER (ORDER BY date_id ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as rolling_7d_drift
FROM daily_bal
ORDER BY date_id;

-- =========================================================
-- FINAL VERDICT QUERY (The "Physics" Report)
-- =========================================================

SELECT 'Conversion Physics (Demand)' as check_type, COUNT(*) as failures FROM validation.violation_physics_demand_overflow
UNION ALL
SELECT 'Saturation Physics (Scaling)', COUNT(*) FROM validation.violation_physics_infinite_scaling
UNION ALL
SELECT 'Attribution Physics (Skew)', COUNT(*) FROM validation.violation_physics_attribution_skew
UNION ALL
SELECT 'Mass Balance (Rolling Drift)', COUNT(*) FROM validation.violation_physics_rolling_mass_balance WHERE ABS(rolling_7d_drift) > 500;