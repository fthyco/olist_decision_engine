import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import os
import sys
import zlib

# ==========================================
# SETUP
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
import db_config
engine = db_config.get_engine()

class OlistMasterEngineV5:
    def __init__(self, difficulty, output_folder):
        self.output_folder = output_folder
        self.seed = {'Easy': 101, 'Medium': 202, 'Hard': 404}.get(difficulty, 42)
        np.random.seed(self.seed)
        os.makedirs(output_folder, exist_ok=True)
        
        # --- 1. CONFIGURATION LAYER (No Hardcoding) ---
        self.params = self._get_params(difficulty)
        print(f"🚀 MASTER ENGINE V5 INITIALIZED | Mode: {difficulty}")
        print(f"   -> Params: {self.params}")

    def _get_params(self, difficulty):
        # Base Parameters
        p = {
            'spend_mult': 1.0, 
            'ad_eff': 1.0,      # 1.0 = Normal Efficiency
            'base_burn': 0.2,   # 20% Base Funnel Loss
            'org_base': 0.30,   # 30% Organic Traffic
            'chaos_level': 0.05, 
            'missing_data_prob': 0.01,
            # Ops Params 
            'ops_base': 1.5,
            'ops_item': 0.5,
            'weekend_tax': 1.0,
            'freight_markup': 1.1
        }
        
        if difficulty == 'Medium':
            p.update({
                'spend_mult': 1.5, 
                'base_burn': 0.3,
                'org_base': 0.20,
                'chaos_level': 0.15, 
                'missing_data_prob': 0.05,
                'ops_base': 2.0,
                'freight_markup': 1.25
            })
        elif difficulty == 'Hard':
            p.update({
                'spend_mult': 2.5, 
                'ad_eff': 0.5,      # Low Efficiency -> Will spike Burn Rate
                'base_burn': 0.4,   # High Base Burn
                'org_base': 0.10,   # SEO Dead
                'chaos_level': 0.30, 
                'missing_data_prob': 0.10,
                'ops_base': 3.5,
                'ops_item': 1.0,
                'weekend_tax': 1.5, # Penalize Weekends
                'freight_markup': 1.6
            })
        return p

    # ======================================================
    # PHASE 1: LOAD CONTEXT
    # ======================================================
    def load_context(self):
        print("1. Loading World Context...")
        
        # Timeline
        self.df_timeline = pd.read_sql("SELECT date_id, date, day_name, is_weekend FROM dwh.dim_date WHERE date BETWEEN '2017-01-01' AND '2018-08-31'", engine)
        self.df_timeline['date'] = pd.to_datetime(self.df_timeline['date'])
        self._calculate_seasonality()
        
        # Sellers (Commission Tiers)
        print("   -> Loading Seller Profiles...")
        self.df_sellers = pd.read_sql("SELECT seller_id, seller_state FROM dwh.dim_sellers", engine)
        self.df_sellers['comm_rate'] = np.where(self.df_sellers['seller_state'].isin(['SP', 'RJ']), 0.10, 0.15)
        self.seller_map = self.df_sellers.set_index('seller_id')['comm_rate'].to_dict()

        # Products (Traps)
        print("   -> Loading Product Metadata...")
        self.df_products = pd.read_sql("SELECT product_id, category, product_weight_g FROM dwh.dim_products", engine)
        self.df_products['is_trap'] = (self.df_products['category'].str.contains('furniture', case=False, na=False)) & (self.df_products['product_weight_g'] > 5000)
        self.product_trap_map = self.df_products.set_index('product_id')['is_trap'].to_dict()

    def _calculate_seasonality(self):
        def get_wave(dt):
            val = 1.0
            if dt.month == 11 and 20 <= dt.day <= 26: val = 4.0 
            elif dt.month == 12 and dt.day <= 20: val = 1.8    
            if dt.dayofweek == 0: val *= 1.1 
            elif dt.dayofweek == 5: val *= 0.8 
            return val
        self.df_timeline['seasonality'] = self.df_timeline['date'].apply(get_wave)

    def simulate_marketing(self):
        print("2. Simulating Marketing Ecosystem...")
        channels = {
            'Facebook': {'budget': 2000, 'cpc': 0.5},
            'Google':   {'budget': 3500, 'cpc': 0.8},
            'Email':    {'budget': 500,  'cpc': 0.1},
            'Influencer': {'budget': 1000, 'cpc': 1.5}
        }
        
        self.pool = {d: {} for d in self.df_timeline['date_id'].values}
        mkt_rows = []
        dates = self.df_timeline['date_id'].values
        
        for ch, conf in channels.items():
            # Spend Physics
            noise = np.clip(np.random.normal(1, 0.1, len(dates)), 0.8, 1.2)
            spend = conf['budget'] * self.params['spend_mult'] * self.df_timeline['seasonality'] * noise
            
            # CPC Physics (Efficiency affects Cost)
            real_cpc = (conf['cpc'] / self.params['ad_eff']) * np.random.normal(1, 0.1, len(dates))
            clicks = (spend / real_cpc).astype(int)
            
            # Lag Logic (Weighted Cost Averaging)
            weights = [0.6, 0.3, 0.1]
            for i, c in enumerate(clicks):
                if c <= 0: continue
                unit_cost = real_cpc[i]
                for lag, w in enumerate(weights):
                    if i + lag < len(dates):
                        target_date = dates[i + lag]
                        lagged_clicks = int(c * w)
                        if lagged_clicks == 0: continue
                        
                        if ch not in self.pool[target_date]:
                            self.pool[target_date][ch] = {'clicks': 0, 'total_cost': 0.0}
                        
                        self.pool[target_date][ch]['clicks'] += lagged_clicks
                        self.pool[target_date][ch]['total_cost'] += (lagged_clicks * unit_cost)

            df_ch = pd.DataFrame({'date_id': dates, 'channel': ch, 'spend': spend, 'clicks': clicks})
            mkt_rows.append(df_ch)
            
        self.df_marketing = pd.concat(mkt_rows)

    # ======================================================
    # PHASE 3: ATTRIBUTION (The Bridge)
    # ======================================================
    def run_attribution_engine(self):
        print("3. Attribution Loop (Dynamic Burn Rate)...")
        
        # --- [FIX 1] Clean SQL & Granularity ---
        # We aggregate to Order Level for attribution, but keep Item Count for Ops
        q = """
            SELECT 
                o.order_id, 
                o.date_id, 
                MAX(i.seller_id) as seller_id, 
                MAX(i.product_id) as main_product_id, -- Trap Logic uses main product
                SUM(i.price) as price, 
                SUM(i.freight_value) as freight_value,
                COUNT(i.product_id) as items_count
            FROM dwh.fact_orders o
            JOIN dwh.fact_orders i ON o.order_id = i.order_id
            WHERE o.date_id BETWEEN 20170101 AND 20180831
            GROUP BY o.order_id, o.date_id
            ORDER BY o.date_id
        """
        df_orders = pd.read_sql(q, engine)
        
        # Context Mapping
        df_orders['is_trap_product'] = df_orders['main_product_id'].map(self.product_trap_map).fillna(False)
        df_orders['comm_rate'] = df_orders['seller_id'].map(self.seller_map).fillna(0.20)

        # Vectorized Attribution
        channel_col = np.empty(len(df_orders), dtype=object)
        cac_col = np.zeros(len(df_orders), dtype=float)
        

        efficiency_penalty = (1.0 - self.params['ad_eff']) * 0.5 
        effective_burn_rate = self.params['base_burn'] + efficiency_penalty
        effective_burn_rate = min(0.90, effective_burn_rate) # Cap at 90% waste
        
        print(f"   -> Effective Funnel Burn Rate: {effective_burn_rate:.2%}")

        gb = df_orders.groupby('date_id')
        for date_id, group in gb:
            indices = group.index
            n = len(group)
            day_pool = self.pool.get(date_id, {})
            
            # Prepare Active Channels
            active = []
            for ch, data in day_pool.items():
                if data['clicks'] > 0:
                    active.append({'name': ch, 'clicks': data['clicks'], 'unit_cost': data['total_cost']/data['clicks']})
            
            batch_ch = []
            batch_cac = []
            
            for _ in range(n):
                if np.random.random() < self.params['org_base']:
                    batch_ch.append('Direct/Organic')
                    batch_cac.append(0.0)
                    continue

                if active:
                    # Weighted Choice
                    counts = [x['clicks'] for x in active]
                    probs = np.array(counts) / sum(counts)
                    chosen_idx = np.random.choice(len(active), p=probs)
                    chosen = active[chosen_idx]
                    
                    # Consume
                    chosen['clicks'] -= 1
                    if chosen['clicks'] <= 0: active.pop(chosen_idx)
                    
                    # Burn Logic (Funnel Loss)
                    if np.random.random() > effective_burn_rate:
                        # Converted
                        batch_ch.append(chosen['name'])
                        batch_cac.append(chosen['unit_cost'])
                    else:
                        # Wasted (Bounce)
                        batch_ch.append('Direct/Organic') # Order happened, but attributed to Organic
                        batch_cac.append(0.0) # Cost is recorded in Marketing Table (Spend), but not here (CAC)
                else:
                    batch_ch.append('Direct/Organic')
                    batch_cac.append(0.0)
            
            channel_col[indices] = batch_ch
            cac_col[indices] = batch_cac
            
        df_orders['marketing_channel'] = channel_col
        df_orders['acquisition_cost'] = cac_col
        self.df_processed = df_orders

    # ======================================================
    # PHASE 4: FINANCE & CHAOS
    # ======================================================
    def calculate_financials(self):
        print("4. Calculating Final Financials (Restored Ops Logic)...")
        df = self.df_processed.copy()
        
        # Logistics (Trap Aware)
        df['dist_noise'] = df['order_id'].apply(lambda x: (zlib.crc32(str(x).encode()) % 100)/100.0)
        def calc_carrier(row):
            base = row['freight_value'] * self.params['freight_markup']
            if row['is_trap_product']: return row['freight_value'] * 2.5
            return base + (row['dist_noise'] * 2)
        df['carrier_cost'] = df.apply(calc_carrier, axis=1)
        
        # --- [FIX 4] Ops Cost (Restored Logic) ---
        wk_map = self.df_timeline.set_index('date_id')['is_weekend'].to_dict()
        df['is_weekend'] = df['date_id'].map(wk_map).fillna(False)
        
        # Base + Item Cost
        base_ops_calc = self.params['ops_base'] + (df['items_count'] * self.params['ops_item'])
        # Weekend Tax
        df['ops_cost'] = np.where(df['is_weekend'], base_ops_calc * self.params['weekend_tax'], base_ops_calc)
        
        # Commission & Net
        df['commission_revenue'] = df['price'] * df['comm_rate']
        df['net_profit'] = (df['commission_revenue'] + (df['freight_value'] - df['carrier_cost']) - df['ops_cost'] - df['acquisition_cost'])
        
        # Inject Data Quality Issues (Chaos)
        mask_pixel = np.random.rand(len(df)) < self.params['chaos_level']
        df.loc[mask_pixel, 'marketing_channel'] = 'Unknown'
        
        self.df_final_orders = df

# ======================================================
    # PHASE 5: EXPORT (DUAL WRITE STRATEGY)
    # ======================================================
    def export(self):
        print("5. Exporting Data (Dual Location)...")
        
        run_folder = self.output_folder
        
        dwh_folder = os.path.join(project_root, "dwh(ready_to_be_analyzed)")
        os.makedirs(dwh_folder, exist_ok=True)
        
        print(f"   📂 Run Output: {run_folder}")
        print(f"   📂 DWH Update: {dwh_folder}")

        # -------------------------------------------------------
        # STEP A: Prepare Data Frames
        # -------------------------------------------------------
        
        # 1. Marketing Data
        df_mkt_export = self.df_marketing.copy()
        if np.random.random() < self.params['missing_data_prob']:
            drop_days = np.random.choice(df_mkt_export['date_id'].unique(), size=5)
            print(f"      ⚠️  CHAOS: Removed Marketing Data for days: {drop_days}")
            df_mkt_export = df_mkt_export[~df_mkt_export['date_id'].isin(drop_days)]

        # 2. Financial Data
        cols = ['order_id', 'date_id', 'marketing_channel', 'price', 'acquisition_cost', 'carrier_cost', 'ops_cost', 'net_profit']
        df_fin_export = self.df_final_orders[cols].copy()

        # -------------------------------------------------------
        # STEP B: WRITE TO RUN FOLDER (For GUI History)
        # -------------------------------------------------------
        print("   -> Saving to History Folder (GUI)...")
        df_mkt_export.round(2).to_csv(os.path.join(run_folder, "fact_marketing_daily.csv"), index=False)
        df_fin_export.round(2).to_csv(os.path.join(run_folder, "fact_financials.csv"), index=False)

        # -------------------------------------------------------
        # STEP C: WRITE TO DWH FOLDER (For Analysis)
        # -------------------------------------------------------
        print("   -> Updating Master DWH Folder...")
        df_mkt_export.round(2).to_csv(os.path.join(dwh_folder, "fact_marketing_daily.csv"), index=False)
        df_fin_export.round(2).to_csv(os.path.join(dwh_folder, "fact_financials.csv"), index=False)

        # -------------------------------------------------------
        # STEP D: Export Static Dimensions & Reviews (To DWH Folder Only)
        # -------------------------------------------------------
        
        tables_to_export = {
            'dim_date': "SELECT * FROM dwh.dim_date WHERE date BETWEEN '2017-01-01' AND '2018-08-31'",
            'dim_products': "SELECT * FROM dwh.dim_products",
            'dim_sellers': "SELECT * FROM dwh.dim_sellers",
            'dim_customers': "SELECT * FROM dwh.dim_customers",
        }
        
        for name, query in tables_to_export.items():
            try:
                df_table = pd.read_sql(query, engine)
                df_table.to_csv(os.path.join(dwh_folder, f"{name}.csv"), index=False)
            except Exception as e:
                print(f"      ❌ Error exporting {name}: {e}")

        print(f"✅ EXPORT COMPLETE.")
              
if __name__ == "__main__":
    sim = OlistMasterEngineV5("Hard", "Final_Output_V5")
    sim.load_context()
    sim.simulate_marketing()
    sim.run_attribution_engine()
    sim.calculate_financials()
    sim.export()