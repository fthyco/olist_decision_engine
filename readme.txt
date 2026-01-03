TO RUN IT :
01_LAUNCH_PIPELINE.bat ---> 02_THE_GAME.bat

OLIST DECISION ENGINE
====================

Purpose
-------
This project is a full causal business simulation and decision engine built on top of the Olist dataset.
It simulates market behavior, attribution, unit economics, and full P&L to produce analyst- and CFO-grade outputs.

This is not a demo.
This is a controllable system for signal extraction under noise.

--------------------------------------------------

Project Structure
-----------------

/pipeline
    01_setup_infrastructure.py
    02_build_dwh_schema.py
    03_market_engine.py
    04_attribution_bridge.py
    05_unified_financials.py

/generator_app
    training_engine.py
    training_gui.py

/data
    Raw Olist CSV datasets

/json_source
    Generated JSON artifacts used by simulation

/dwh(ready_to_be_analyzed)
    Final analytical outputs (facts & dimensions)

/Training_Output
    Per-run simulation history (GUI runs)

/Validation_engine
    Physics, causality, and integrity checks

run_pipeline.py
    CLI entry point (headless execution)

db_config.py
    Database connection config (DO NOT hardcode secrets)

--------------------------------------------------

System Requirements
-------------------

- Python 3.10+
- PostgreSQL 13+
- Windows (GUI uses Tkinter)

Python packages:
- pandas
- numpy
- sqlalchemy
- psycopg2-binary
- tkinter

Install dependencies:
pip install -r requirements.txt

--------------------------------------------------

Database Setup
--------------

1. PostgreSQL must be running.
2. Create a database user with full privileges.
3. Configure database access via environment variables
   OR copy db_config.sample.py to db_config.py and edit locally.

Required privileges:
- CREATE DATABASE
- CREATE SCHEMA
- CREATE TABLE
- INSERT / UPDATE / DELETE

--------------------------------------------------

Execution Modes
---------------

MODE 1: Full Pipeline (CLI)

Runs the complete ETL + simulation pipeline sequentially.

Command:
python run_pipeline.py

Execution order:
1. Infrastructure & raw ingestion
2. Data warehouse schema
3. Marketing simulation
4. Attribution bridge
5. Financials & P&L

--------------------------------------------------

MODE 2: Simulation Engine (GUI)

Graphical control center for scenario-based simulations.

Command:
python generator_app/training_gui.py

Outputs:
- Training_Output/<scenario_name>/
- dwh(ready_to_be_analyzed)/ updated

--------------------------------------------------

Final Outputs
-------------

Core analytical tables:

- dwh.fact_marketing_daily
- dwh.fact_orders (with attribution)
- dwh.fact_financials
- dwh.fact_daily_pnl
- dwh.fact_seller_subscriptions

These tables are designed for direct BI consumption
(Power BI, Tableau, SQL, Python).

--------------------------------------------------

Design Principles
-----------------

- Deterministic randomness (reproducible chaos)
- Explicit causality (no black-box randomness)
- Conservation laws (demand, spend, attribution)
- Separation of concerns (infra, market, attribution, finance)
- Analyst-first outputs

--------------------------------------------------

Warnings
--------

- Do NOT commit db_config.py with real credentials.
- Do NOT run against production databases.
- Do NOT modify pipeline order unless you understand dependencies.

--------------------------------------------------

Author Intent
-------------

This system exists to test thinking, not tools.
If the outputs look clean, the system is lying.
If the outputs look messy but explainable, the system is alive.
