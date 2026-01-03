import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import os
import sys

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

print("🚀 Phase 4: Constructing Causal Attribution Bridge...")

# ==========================================
# 1. LOAD SUPPLY & DEMAND
# ==========================================
print("   📥 Loading Market Supply (Clicks) & Market Demand (Orders)...")

# A. Supply: Marketing Activity (From Phase 3)
q_mkt = """
    SELECT date_id, channel, clicks, spend
    FROM dwh.fact_marketing_daily
    WHERE clicks > 0
    ORDER BY date_id
"""
df_supply = pd.read_sql(q_mkt, engine)

# B. Demand: Real Orders (From Phase 1 & 2)
q_demand = """
    SELECT order_id, date_id 
    FROM dwh.fact_orders
    ORDER BY date_id, order_id
"""
df_demand = pd.read_sql(q_demand, engine)

print(f"      -> Supply: {df_supply['clicks'].sum():,} Potential Clicks")
print(f"      -> Demand: {len(df_demand):,} Real Orders")

# ==========================================
# 2. INVENTORY MANAGEMENT (The Core Logic)
# ==========================================

print("   ⚙️  Initializing Inventory System...")

# Pivot table for fast lookup
# Index: date_id, Columns: channels, Values: clicks
inventory_df = df_supply.pivot(index='date_id', columns='channel', values='clicks').fillna(0)
inventory_map = inventory_df.to_dict('index')

# Channels list
channels = list(inventory_df.columns)

# ==========================================
# 3. ATTRIBUTION LOOP (Stateful Matching)
# ==========================================
print("   🔗 Running Attribution Engine (Window: 3 Days)...")

attribution_results = []
organic_count = 0
paid_count = 0
wasted_clicks = 0

# Group orders by date for batch processing
daily_orders = df_demand.groupby('date_id')['order_id'].apply(list).to_dict()

# الحصول على قائمة التواريخ المرتبة
all_dates = sorted(daily_orders.keys())

for current_date in all_dates:
    orders_today = daily_orders[current_date]
    n_orders = len(orders_today)
    
    if n_orders == 0: continue

    # --- Step A: Build Daily Pool (Inventory + Decay) ---
    
    daily_pool = {ch: 0 for ch in channels}
    
    # Lookback logic
    for lag in range(3): 
        try:
            curr_dt = pd.to_datetime(str(current_date), format='%Y%m%d')
            target_dt = curr_dt - pd.Timedelta(days=lag)
            target_date_id = int(target_dt.strftime('%Y%m%d'))
        except:
            continue
            
        if target_date_id in inventory_map:
            day_clicks = inventory_map[target_date_id]
            weight = 1.0 / (lag + 1) # Decay factor: 1.0, 0.5, 0.33
            
            for ch, clicks in day_clicks.items():
                daily_pool[ch] += (clicks * weight)

    # --- Step B: Attribution (Weighted Random) ---
    total_available_clicks = sum(daily_pool.values())
    
    assigned_channels_today = []
    
    if total_available_clicks < 1:
        assigned_channels_today = ['Direct/Organic'] * n_orders
        organic_count += n_orders
    
    else:

        probs = []
        valid_channels = []
        for ch in channels:
            if daily_pool[ch] > 0:
                valid_channels.append(ch)
                probs.append(daily_pool[ch])
        
        # Normalize probabilities
        probs = np.array(probs)
        probs = probs / probs.sum()
        
        # Scenario 1: Abundance (Clicks > Orders)
        if total_available_clicks >= n_orders:
            choices = np.random.choice(valid_channels, size=n_orders, p=probs)
            assigned_channels_today = choices
            paid_count += n_orders
            
        # Scenario 2: Scarcity (Orders > Clicks)
        else:
            n_paid = int(total_available_clicks)
            n_organic = n_orders - n_paid
            
            # Paid Part
            if n_paid > 0:
                paid_choices = np.random.choice(valid_channels, size=n_paid, p=probs)
                assigned_channels_today.extend(paid_choices)
                paid_count += n_paid
            
            # Organic Part
            assigned_channels_today.extend(['Direct/Organic'] * n_organic)
            organic_count += n_organic

    # --- Step C: Register Results ---
    for i, order_id in enumerate(orders_today):
        attribution_results.append({
            'order_id': order_id,
            'marketing_channel': assigned_channels_today[i]
        })

# ==========================================
# 4. UPDATE DATABASE (Bulk Action)
# ==========================================
print(f"   📊 Attribution Summary:")
print(f"      -> Paid Acquisition: {paid_count:,} orders")
print(f"      -> Organic/Direct:   {organic_count:,} orders")
print("   💾 Updating 'dwh.fact_orders' with attribution data...")

# Create Temp Table for Fast Update
df_attr = pd.DataFrame(attribution_results)
df_attr.to_sql('temp_attribution', engine, if_exists='replace', index=False)

with engine.begin() as conn:
    # 1. Add Index to Temp Table
    conn.execute(text("CREATE INDEX idx_temp_attr ON temp_attribution(order_id)"))
    
    # 2. Update Fact Table
    conn.execute(text("""
        UPDATE dwh.fact_orders f
        SET marketing_channel = t.marketing_channel
        FROM temp_attribution t
        WHERE f.order_id = t.order_id
    """))
    
    # 3. Clean up
    conn.execute(text("DROP TABLE temp_attribution"))

print("🎉 Phase 4 Complete: The Bridge is Built.")
print("   Now every order has a source based on market availability.")