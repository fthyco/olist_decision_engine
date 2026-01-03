import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.types import Integer, String, Numeric, Float
import os
import sys
import zlib

# ==========================================
# 1. SETUP PATHS & DB CONNECTION
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

import db_config

engine = db_config.get_engine()
SEED = 42
np.random.seed(SEED)

print("🚀 Phase 5 (Final): Unified Financials with Real P&L & Wasted Spend...")

# ==========================================
# PART 1: DETERMINISTIC SELLER COMMISSIONS
# ==========================================

print("   🔒 1. Assigning Deterministic Commission Rates...")

def get_stable_commission(seller_id):

    val = zlib.adler32(seller_id.encode('utf-8'))
    mod = val % 100
    if mod < 20: return 0.10      # Enterprise / Top
    elif mod < 80: return 0.15    # Standard
    else: return 0.20             # Risky / New

df_sellers = pd.read_sql("SELECT seller_id FROM dwh.dim_sellers", engine)
df_sellers['comm_rate'] = df_sellers['seller_id'].apply(get_stable_commission)
seller_rate_map = df_sellers.set_index('seller_id')['comm_rate'].to_dict()

# ==========================================
# PART 2: MARKETING WASTE CALCULATION
# ==========================================
print("   💸 2. Calculating Marketing Efficiency & Wasted Spend...")

# 1. Total Spend per Day (Real Cash Out)
df_daily_spend = pd.read_sql("""
    SELECT date_id, SUM(spend) as total_marketing_spend
    FROM dwh.fact_marketing_daily
    GROUP BY 1
""", engine)

# 2. Attributed Spend (Effective CAC)

# ==========================================
# PART 3: OPERATIONAL FINANCIALS (Order Level)
# ==========================================
print("   📦 3. Processing Transactional Financials...")

# A. Load Data
q_ops = """
    SELECT 
        o.order_id, o.date_id, o.marketing_channel, o.order_status,
        o.order_purchase_timestamp, o.order_estimated_delivery_date, o.order_delivered_customer_date,
        i.seller_id, i.price, i.freight_value, i.order_item_id
    FROM dwh.fact_orders o
    JOIN public.raw_order_items i ON o.order_id = i.order_id
"""
df_ops = pd.read_sql(q_ops, engine)

# B. Calculate Unit Metrics
df_ops['order_purchase_timestamp'] = pd.to_datetime(df_ops['order_purchase_timestamp'])
df_ops['order_estimated_delivery_date'] = pd.to_datetime(df_ops['order_estimated_delivery_date'])
df_ops['order_delivered_customer_date'] = pd.to_datetime(df_ops['order_delivered_customer_date'])

df_ops['actual_days'] = (df_ops['order_delivered_customer_date'] - df_ops['order_purchase_timestamp']).dt.days.fillna(0)
df_ops['estimated_days'] = (df_ops['order_estimated_delivery_date'] - df_ops['order_purchase_timestamp']).dt.days.fillna(0)

# C. Calculate Unit CAC (Attributed Only)
df_mkt_daily = pd.read_sql("SELECT date_id, channel, spend FROM dwh.fact_marketing_daily", engine)
df_orders_daily = pd.read_sql("SELECT date_id, marketing_channel as channel, COUNT(order_id) as orders FROM dwh.fact_orders GROUP BY 1,2", engine)

df_cac_calc = pd.merge(df_mkt_daily, df_orders_daily, on=['date_id', 'channel'], how='left').fillna(0)
# CAC = Spend / Orders. If Orders=0, CAC is technically Infinite (Pure Waste).
# We handle Pure Waste in the Daily P&L table, not here.
df_cac_calc['unit_cac'] = np.where(df_cac_calc['orders'] > 0, df_cac_calc['spend'] / df_cac_calc['orders'], 0)
cac_map = df_cac_calc.set_index(['date_id', 'channel'])['unit_cac'].to_dict()

# Distribute CAC to items weighted by Price
df_ord_gmv = df_ops.groupby('order_id')['price'].sum().reset_index().rename(columns={'price': 'total_gmv'})
df_ops = df_ops.merge(df_ord_gmv, on='order_id')
df_ops['gmv_share'] = df_ops['price'] / df_ops['total_gmv']

def get_allocated_cac(row):
    # Direct/Organic is always 0
    if row['marketing_channel'] == 'Direct/Organic': return 0.0
    
    # Get Unit CAC for the channel on that day
    base_cac = cac_map.get((row['date_id'], row['marketing_channel']), 0.0)
    return base_cac * row['gmv_share']

df_ops['acquisition_cost'] = df_ops.apply(get_allocated_cac, axis=1)

# D. Financials
df_ops['comm_rate'] = df_ops['seller_id'].map(seller_rate_map).fillna(0.15)
df_ops['commission_revenue'] = np.where(df_ops['order_status']=='delivered', df_ops['price'] * df_ops['comm_rate'], 0.0)

# Logistics (Olist pays carrier cost + 10%, collects freight_value)
df_ops['carrier_cost'] = df_ops['freight_value'] * 1.10
df_ops['logistics_margin'] = df_ops['freight_value'] - df_ops['carrier_cost']
df_ops['ops_cost'] = 1.50

# Penalties
is_late = (df_ops['actual_days'] > df_ops['estimated_days'] + 2) & (df_ops['order_status']=='delivered')
df_ops['sla_penalty'] = np.where(is_late, df_ops['freight_value'] * 0.5, 0.0)

# Net Contribution (Unit Level)
df_ops['net_contribution'] = (
    df_ops['commission_revenue'] + 
    df_ops['logistics_margin'] - 
    df_ops['ops_cost'] - 
    df_ops['sla_penalty'] - 
    df_ops['acquisition_cost']
)

# ==========================================
# PART 4: DAILY P&L (The Truth Table)
# ==========================================
print("   📊 4. Generating Fact Daily P&L (Aggregating Waste)...")

# 1. Aggregate Operational Results
df_daily_ops = df_ops.groupby('date_id').agg({
    'commission_revenue': 'sum',
    'logistics_margin': 'sum',
    'ops_cost': 'sum',
    'sla_penalty': 'sum',
    'acquisition_cost': 'sum'  # This is "Effective CAC"
}).reset_index()

# 2. Merge with Total Marketing Spend
df_pnl = pd.merge(df_daily_spend, df_daily_ops, on='date_id', how='outer').fillna(0)

# 3. Calculate "Wasted Spend" & Net P&L
# Wasted Spend = (Total Cash Out) - (Effective CAC assigned to orders)
df_pnl['marketing_waste'] = df_pnl['total_marketing_spend'] - df_pnl['acquisition_cost']
df_pnl['marketing_waste'] = df_pnl['marketing_waste'].apply(lambda x: x if x > 0.01 else 0)

# 4. Final Net Result (Bottom Line)
# Net P&L = Commission + Logistics Margin - Ops - Penalty - TOTAL SPEND (Not just CAC)
df_pnl['net_profit_loss'] = (
    df_pnl['commission_revenue'] + 
    df_pnl['logistics_margin'] - 
    df_pnl['ops_cost'] - 
    df_pnl['sla_penalty'] - 
    df_pnl['total_marketing_spend'] 
)

# ==========================================
# PART 5: SAAS REVENUE (Subscriptions)
# ==========================================
print("   💳 5. Calculating SaaS Revenue...")
# ... (Same Logic as before, kept for completeness) ...
df_ops['month_id'] = df_ops['order_purchase_timestamp'].dt.to_period('M')
seller_monthly = df_ops.groupby(['seller_id', 'month_id'])['price'].sum().reset_index()
subs_ledger = []
for seller_id, group in seller_monthly.groupby('seller_id'):
    group = group.set_index('month_id').sort_index()
    full_range = pd.period_range(start=group.index.min(), end=group.index.max(), freq='M')
    group = group.reindex(full_range).fillna(0)
    group['rolling_gmv'] = group['price'].rolling(3, min_periods=1).mean()
    for period, row in group.iterrows():
        gmv = row['rolling_gmv']
        if gmv > 10000: tier, fee = 'Enterprise', 999.90
        elif gmv > 2000: tier, fee = 'Pro', 199.90
        else: tier, fee = 'Basic', 49.90
        subs_ledger.append({'date_id': int(period.start_time.strftime('%Y%m01')), 'seller_id': seller_id, 'plan_type': tier, 'subscription_fee': fee})
df_subs = pd.DataFrame(subs_ledger)

# ==========================================
# PART 6: SAVE
# ==========================================
print("   💾 Saving Tables...")

# 1. Fact Financials (Transaction Level - Unit Economics)
cols_fin = ['order_id', 'seller_id', 'date_id', 'marketing_channel', 'price', 'acquisition_cost', 'commission_revenue', 'net_contribution']
df_ops[cols_fin].round(2).to_sql('fact_financials', engine, schema='dwh', if_exists='replace', index=False, chunksize=5000)

# 2. Fact Daily P&L (Business Level - Includes Waste)
# This is the NEW table for CFO view
df_pnl.round(2).to_sql('fact_daily_pnl', engine, schema='dwh', if_exists='replace', index=False)

# 3. Subscriptions
df_subs.to_sql('fact_seller_subscriptions', engine, schema='dwh', if_exists='replace', index=False)

print("🎉 DONE. Check 'fact_daily_pnl' for Wasted Spend analysis.")