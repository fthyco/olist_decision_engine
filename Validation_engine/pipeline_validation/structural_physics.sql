CREATE OR REPLACE VIEW validation.violation_grain_duplication AS
SELECT order_id, order_item_id, COUNT(*) as frequency FROM validation.snap_fact_orders GROUP BY 1, 2 HAVING COUNT(*) > 1;

CREATE OR REPLACE VIEW validation.violation_organic_spend AS
SELECT * FROM validation.snap_fact_marketing WHERE channel IN ('Organic_SEO', 'Direct', 'Referral') AND spend > 0;