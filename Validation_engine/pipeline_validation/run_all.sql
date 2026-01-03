CREATE SCHEMA IF NOT EXISTS validation;

-- =========================================================
-- 0. SNAPSHOTS
-- =========================================================
DROP TABLE IF EXISTS validation.snap_fact_orders CASCADE;
CREATE TABLE validation.snap_fact_orders AS SELECT * FROM dwh.fact_orders;

DROP TABLE IF EXISTS validation.snap_fact_marketing CASCADE;
CREATE TABLE validation.snap_fact_marketing AS SELECT * FROM dwh.fact_marketing_daily;

DROP TABLE IF EXISTS validation.snap_fact_financials CASCADE;
CREATE TABLE validation.snap_fact_financials AS SELECT * FROM dwh.fact_financials;

-- =========================================================
-- 1. STATEFUL CAUSALITY CHECKS
-- =========================================================

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

-- =========================================================
-- 2. FINANCIAL PHYSICS (DRIFT CLASSIFICATION)
-- =========================================================

-- CHECK C: Drift Diagnostic
CREATE OR REPLACE VIEW validation.violation_financial_drift_analysis AS
WITH drift_base AS (
    SELECT 
        COALESCE(m.date_id, f.date_id) as date_id,
        COALESCE(m.spend, 0) as platform_spend,
        COALESCE(f.acquisition_cost, 0) as ledger_cost,
        (COALESCE(m.spend, 0) - COALESCE(f.acquisition_cost, 0)) as drift_amount
    FROM (SELECT date_id, SUM(spend) as spend FROM validation.snap_fact_marketing GROUP BY 1) m
    FULL OUTER JOIN (SELECT date_id, SUM(acquisition_cost) as acquisition_cost FROM validation.snap_fact_financials GROUP BY 1) f
        ON m.date_id = f.date_id
)
SELECT 
    date_id,
    drift_amount,
    CASE 
        WHEN ABS(drift_amount) < 1.0 THEN 'Rounding Noise'
        WHEN platform_spend > 0 AND ledger_cost = 0 THEN 'Unallocated Waste (Critical)'
        WHEN platform_spend = 0 AND ledger_cost > 0 THEN 'Phantom Cost (Critical)'
        ELSE 'Allocation Logic Error' 
    END as drift_category,
    CASE 
        WHEN ABS(drift_amount) > 1000 THEN 'High Impact'
        ELSE 'Low Impact'
    END as monetary_severity
FROM drift_base
WHERE ABS(drift_amount) > 0.01;

-- =========================================================
-- 3. STRUCTURAL PHYSICS (The Classics)
-- =========================================================

CREATE OR REPLACE VIEW validation.violation_grain_duplication AS
SELECT order_id, order_item_id, COUNT(*) as frequency FROM validation.snap_fact_orders GROUP BY 1, 2 HAVING COUNT(*) > 1;

CREATE OR REPLACE VIEW validation.violation_organic_spend AS
SELECT * FROM validation.snap_fact_marketing WHERE channel IN ('Organic_SEO', 'Direct', 'Referral') AND spend > 0;

-- =========================================================
-- 4. THE JUDGMENT REPORT
-- =========================================================

SELECT 
    'Causal: Impossible Orders (No AdStock)' as violation_type,
    COUNT(*) as incident_count,
    COALESCE(SUM(revenue_at_risk), 0) as financial_impact_value,
    'Revoke Attribution' as recommended_action
FROM validation.violation_causal_impossible_orders

UNION ALL

SELECT 
    'Temporal: Future Leakage',
    COUNT(*),
    0 as financial_impact_value,
    'Fix Timezone/ETL Logic'
FROM validation.violation_temporal_future_leakage

UNION ALL

SELECT 
    'Financial: ' || drift_category,
    COUNT(*),
    SUM(ABS(drift_amount)),
    'Audit Allocation Algo'
FROM validation.violation_financial_drift_analysis
GROUP BY 1

UNION ALL

SELECT 
    'Structural: Grain Violation',
    COUNT(*),
    0,
    'Deduplicate Source'
FROM validation.violation_grain_duplication;