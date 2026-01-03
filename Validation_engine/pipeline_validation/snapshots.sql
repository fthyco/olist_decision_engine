DROP TABLE IF EXISTS validation.snap_fact_orders CASCADE;
CREATE TABLE validation.snap_fact_orders AS SELECT * FROM dwh.fact_orders;

DROP TABLE IF EXISTS validation.snap_fact_marketing CASCADE;
CREATE TABLE validation.snap_fact_marketing AS SELECT * FROM dwh.fact_marketing_daily;

DROP TABLE IF EXISTS validation.snap_fact_financials CASCADE;
CREATE TABLE validation.snap_fact_financials AS SELECT * FROM dwh.fact_financials;