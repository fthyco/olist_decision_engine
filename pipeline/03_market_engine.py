import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.types import Integer, String, Float, Numeric
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

print("🚀 Phase 3: Initializing Causal Market Engine...")

# ==========================================
# 1. LOAD TIMELINE & CONTEXT
# ==========================================
print("   ⏳ Loading Timeline & Seasonality...")

q_dates = """
    SELECT date_id, date, month, is_weekend
    FROM dwh.dim_date 
    WHERE date BETWEEN '2016-09-01' AND '2018-10-31'
    ORDER BY date_id
"""
df_timeline = pd.read_sql(q_dates, engine)
df_timeline['date'] = pd.to_datetime(df_timeline['date'])

def get_seasonality_factor(date):
    month = date.month
    day = date.day 
    factor = 1.0
    
    # Black Friday (Late Nov)
    if month == 11 and 20 <= day <= 28: factor = 3.5 
    # Christmas Rush (Early Dec)
    elif month == 12 and 1 <= day <= 15: factor = 1.8
    # New Year Slump
    elif month == 1: factor = 0.8
    # Valentine's (Feb)
    elif month == 2 and 5 <= day <= 12: factor = 1.3
    # Mothers Day (May)
    elif month == 5 and 1 <= day <= 10: factor = 1.4
    
    # Weekend Dip (B2B drops, B2C spikes, mixed dip)
    if date.dayofweek >= 5: factor *= 0.9
    
    return factor

df_timeline['seasonality'] = df_timeline['date'].apply(get_seasonality_factor)

# ==========================================
# 2. CHANNEL PHYSICS (Brazilian Market Config)
# ==========================================
channels_config = {
    'Facebook_Ads': {
        'base_daily_budget': 85,    
        'cpm': 12.5,                
        'base_ctr': 0.009,          
        'saturation_cap': 80000,    
        'adstock_decay': 0.5,       
        'volatility': 0.3           
    },
    'Google_Search': {
        'base_daily_budget': 120,   
        'cpm': 28.0,                
        'base_ctr': 0.028,          
        'saturation_cap': 40000,    
        'adstock_decay': 0.2,       
        'volatility': 0.1           
    },
    'Influencer_Instagram': {
        'base_daily_budget': 45,    
        'cpm': 35.0,                
        'base_ctr': 0.012,          
        'saturation_cap': 100000,   
        'adstock_decay': 0.8,       
        'volatility': 0.7           
    },
    'Email_Marketing': {
        'base_daily_budget': 15,    
        'cpm': 2.0,                 
        'base_ctr': 0.035,          
        'saturation_cap': 15000,    
        'adstock_decay': 0.3,       
        'volatility': 0.1
    },
    'Organic_SEO': {
        'base_daily_budget': 0,
        'cpm': 0, 
        'base_ctr': 0.05,            
        'saturation_cap': 1000000, 
        'adstock_decay': 0.99, 
        'volatility': 0.05
    }
}
# ==========================================
# 3. SIMULATION ENGINE (Vectorized)
# ==========================================
print("   ⚙️  Running Marketing Simulation (Spend -> AdStock -> Clicks)...")

all_channel_data = []

for channel, params in channels_config.items():
    print(f"      -> Simulating Physics for: {channel}")
    
    df_ch = df_timeline.copy()
    n_days = len(df_ch)
    
    # A. Generate Base Spend (Decision)
    noise = np.random.normal(1, params['volatility'], n_days)
    df_ch['spend'] = params['base_daily_budget'] * df_ch['seasonality'] * noise
    df_ch['spend'] = df_ch['spend'].clip(lower=0) 
    
    # Special Case: Organic has no spend, but "Effort" equivalent
    if channel == 'Organic_SEO':
        df_ch['spend'] = 0
        # Growth over time (SEO takes time to build)
        effort_curve = np.linspace(1, 3, n_days)
        df_ch['raw_impressions'] = 5000 * df_ch['seasonality'] * effort_curve
    else:
        # B. Generate Impressions (Exposure)
        # Impressions = (Spend / CPM) * 1000
        df_ch['raw_impressions'] = (df_ch['spend'] / params['cpm']) * 1000
    
    # C. AdStock Calculation (Memory State)
    # Alpha must be > 0. We use max(0.001, ...) just to be absolutely safe mathematically
    decay_val = params['adstock_decay']
    alpha_val = max(0.001, 1 - decay_val) 
    
    df_ch['ad_stock'] = df_ch['raw_impressions'].ewm(alpha=alpha_val, adjust=False).mean()
    
    # D. Saturation & Diminishing Returns (The Curve)
    # Saturation Factor = 1 / (1 + (AdStock / Capacity)^2)
    # For Organic, cap is high so saturation is low
    cap = params['saturation_cap']
    if cap > 0:
        saturation_ratio = df_ch['ad_stock'] / cap
        df_ch['efficiency_factor'] = 1 / (1 + saturation_ratio**1.5)
    else:
        df_ch['efficiency_factor'] = 1.0
    
    # E. Clicks Calculation (The Output)
    df_ch['effective_ctr'] = params['base_ctr'] * df_ch['efficiency_factor']
    
    # Add noise to CTR
    ctr_noise = np.random.normal(1, 0.1, n_days)
    df_ch['clicks'] = (df_ch['ad_stock'] * df_ch['effective_ctr'] * ctr_noise).astype(int)
    
    # Final Metrics Formatting
    df_ch['impressions'] = df_ch['raw_impressions'].astype(int)
    df_ch['channel'] = channel
    
    # Keep only relevant columns
    cols = ['date_id', 'channel', 'spend', 'impressions', 'clicks', 'effective_ctr', 'ad_stock']
    all_channel_data.append(df_ch[cols])

# Combine all channels
df_marketing = pd.concat(all_channel_data, ignore_index=True)

# ==========================================
# 4. SAVE TO DWH
# ==========================================
print("   💾 Saving to 'dwh.fact_marketing_daily'...")

# Schema Definition
dtype_map = {
    'date_id': Integer(),
    'channel': String(),
    'spend': Numeric(10, 2),
    'impressions': Integer(),
    'clicks': Integer(),
    'effective_ctr': Float(),
    'ad_stock': Float() 
}

# Rounding
df_marketing['spend'] = df_marketing['spend'].round(2)
df_marketing['effective_ctr'] = df_marketing['effective_ctr'].round(4)
df_marketing['ad_stock'] = df_marketing['ad_stock'].round(0)

df_marketing.to_sql('fact_marketing_daily', engine, schema='dwh', if_exists='replace', index=False, dtype=dtype_map)

print(f"   ✅ Generated {len(df_marketing)} marketing records.")
print("🎉 Phase 3 Complete.")