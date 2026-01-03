01_setup_infrastructure.py
Purpose

Initialize the physical data layer of the system.

What this file establishes

Creates the database safely.

Loads raw datasets without transformation.

Preserves reality as-is, before interpretation.

Why it exists

Every analytical system must start from unopinionated truth.
This file draws a hard line between data ingestion and business logic.

No business assumptions are allowed here.

02_build_dwh_schema.py
Purpose

Transform raw reality into a structured analytical universe.

What this file establishes

Defines grain explicitly (order-item level).

Builds dimensions and fact tables.

Introduces time intelligence.

Enforces structural integrity.

Why it exists

This is where the system decides how reality is observed.
Any mistake here propagates as systemic error downstream.

This layer is interpretation, not simulation.

03_market_engine.py
Purpose

Simulate market dynamics over time.

What this file establishes

Marketing spend as a decision, not a metric.

AdStock as market memory.

Saturation and diminishing returns.

Seasonality and volatility.

Why it exists

Real markets have memory.
Clicks do not reset daily.
Spend has delayed and decaying effects.

This file converts static data into a living market.

Without it, attribution becomes statistically dishonest.

04_attribution_bridge.py
Purpose

Bridge market supply to customer demand using stateful logic.

What this file establishes

Clicks treated as inventory.

Orders consume available market supply.

Time-decayed attribution windows.

Acceptance of scarcity and excess.

Why it exists

This breaks the false assumption that
“every order must have a same-day click”.

Attribution here is emergent, not forced.

This is the difference between reporting and modeling.

05_unified_financials.py
Purpose

Produce financial truth at both unit and business level.

What this file establishes

Deterministic seller commissions.

True CAC vs wasted marketing spend.

Unit economics per order item.

Daily P&L including inefficiency.

SaaS subscription revenue logic.

Why it exists

Marketing metrics are irrelevant without profit.

This file forces the system to answer one question only:
Did the business actually make or lose money?

If a system cannot produce P&L, it is not decision-grade.

System Flow Summary

Reality
→ Structured Observation
→ Market Dynamics
→ Causal Attribution
→ Financial Truth

Each file exists because the previous one is insufficient alone.

What this project is NOT

Not a dashboard-first project

Not a visualization exercise

Not a KPI showcase

What this project IS

A causal market emulator

A decision-support system

A financial truth machine