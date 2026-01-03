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