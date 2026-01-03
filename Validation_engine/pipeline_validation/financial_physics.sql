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