import pandas as pd
from sqlalchemy import create_engine, text
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import sys

# ==========================================
# 1. SETUP PATHS & DB CONFIG
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

import db_config

DB_USER = db_config.DB_CONFIG['user']
DB_PASS = db_config.DB_CONFIG['pass']
DB_HOST = db_config.DB_CONFIG['host']
DB_NAME = db_config.DB_CONFIG['db']

engine = db_config.get_engine()

DATA_FOLDER = os.path.join(project_root, "data")
JSON_FOLDER = os.path.join(project_root, "json_source")

print(f"📂 Execution Context: {project_root}")

# ==========================================
# STEP 1: SAFE DB CREATION
# ==========================================
print("\n⚙️  Step 1: Initializing Database Infrastructure...")

try:
    con = psycopg2.connect(dbname='postgres', user=DB_USER, host=DB_HOST, password=DB_PASS)
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    
    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
    if not cur.fetchone():
        cur.execute(f"CREATE DATABASE {DB_NAME}")
        print(f"    ✅ Database '{DB_NAME}' created successfully.")
    else:
        print(f"    ℹ️  Database '{DB_NAME}' already exists.")
    
    cur.close()
    con.close()
except Exception as e:
    print(f"❌ Critical Error in DB Creation: {e}")
    sys.exit(1)

# ==========================================
# STEP 2: LOADING RAW DATA
# ==========================================
files_map = {
    'olist_orders_dataset.csv': 'raw_orders',
    'olist_order_items_dataset.csv': 'raw_order_items',
    'olist_customers_dataset.csv': 'raw_customers',
    'olist_sellers_dataset.csv': 'raw_sellers',
    'olist_products_dataset.csv' : 'raw_products',
    'olist_geolocation_dataset.csv': 'raw_geolocation',
    'product_category_name_translation.csv': 'raw_category_translation',
    'olist_order_payments_dataset.csv': 'raw_payments',
    'olist_order_reviews_dataset.csv': 'raw_reviews'
}

print("\n📥 Step 2: Ingesting Raw Data to 'public' Schema...")

for csv_file, table_name in files_map.items():
    file_path = os.path.join(DATA_FOLDER, csv_file)

    if os.path.exists(file_path):
        try:
            print(f"    ⏳ Ingesting: {table_name}...")
            chunk_size = 10000
            first_chunk = True
            
            for chunk in pd.read_csv(file_path, chunksize=chunk_size):
                mode = 'replace' if first_chunk else 'append'
                chunk.to_sql(table_name, engine, schema='public', if_exists=mode, index=False, method='multi')
                first_chunk = False
            
            print(f"       -> ✅ Success: {table_name}")
        except Exception as e:
            print(f"       -> ❌ Error loading {csv_file}: {e}")
    else:
        print(f"    ⚠️  Warning: File not found ({csv_file})")

# ==========================================
# STEP 3: PREPARING JSON ARTIFACTS
# ==========================================
print("\n📦 Step 3: Generating JSON Artifacts for Simulation...")
os.makedirs(JSON_FOLDER, exist_ok=True)

from sqlalchemy import inspect

try:
    inspector = inspect(engine)
    if inspector.has_table("raw_products", schema="public"):
        df_prod = pd.read_sql("SELECT * FROM public.raw_products", engine)
        json_path = os.path.join(JSON_FOLDER, 'products.json')
        df_prod.to_json(json_path, orient='records', indent=2)
        print(f"    ✅ JSON Dumped: {json_path}")
except Exception as e:
    print(f"    ❌ JSON Error: {e}")

print("\n🎉 PHASE 1 COMPLETE: Infrastructure Ready.")