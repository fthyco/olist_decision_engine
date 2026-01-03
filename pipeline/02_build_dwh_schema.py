import pandas as pd
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

print("🏗️  Phase 2: Constructing Data Warehouse (Schema: dwh)...")

# ==========================================
# 2. SCHEMA CONSTRUCTION
# ==========================================

def exec_sql(conn, query, task_name):
    try:
        conn.execute(text(query))
        print(f"    ✅ {task_name}")
    except Exception as e:
        print(f"    ❌ Failed: {task_name} -> {e}")
        sys.exit(1)

with engine.begin() as conn:
    # 0. Create Schema
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS dwh;"))

    # -------------------------------------------------------
    # 1. DIMENSIONS
    # -------------------------------------------------------
    print("\n   [Dimensions Layer]")
    
    # Dim Products
    q_dim_prod = """
    DROP TABLE IF EXISTS dwh.dim_products;
    CREATE TABLE dwh.dim_products AS
    SELECT 
        p.product_id,
        COALESCE(t.product_category_name_english, p.product_category_name, 'Unknown') as category,
        p.product_weight_g,
        p.product_length_cm,
        p.product_height_cm,
        p.product_width_cm
    FROM public.raw_products p
    LEFT JOIN public.raw_category_translation t 
        ON p.product_category_name = t.product_category_name;
    """
    exec_sql(conn, q_dim_prod, "dim_products")

    # Dim Sellers
    q_dim_sell = """
    DROP TABLE IF EXISTS dwh.dim_sellers;
    CREATE TABLE dwh.dim_sellers AS
    SELECT 
        seller_id, seller_zip_code_prefix, seller_state, seller_city
    FROM public.raw_sellers;
    """
    exec_sql(conn, q_dim_sell, "dim_sellers")

    # Dim Customers
    q_dim_cust = """
    DROP TABLE IF EXISTS dwh.dim_customers;
    CREATE TABLE dwh.dim_customers AS
    SELECT 
        customer_id, customer_unique_id, customer_zip_code_prefix, customer_state, customer_city 
    FROM public.raw_customers;
    """
    exec_sql(conn, q_dim_cust, "dim_customers")

    # -------------------------------------------------------
    # 2. FACTS (The Core)
    # -------------------------------------------------------
    print("\n   [Facts Layer]")

    # Fact Orders (Grain: Item Level)
    q_fact_orders = """
    DROP TABLE IF EXISTS dwh.fact_orders;
    CREATE TABLE dwh.fact_orders AS
    SELECT 
        o.order_id,
        o.customer_id,
        i.product_id,
        i.seller_id,
        i.order_item_id,
        o.order_status,
        o.order_purchase_timestamp::TIMESTAMP as order_purchase_timestamp,
        o.order_approved_at::TIMESTAMP as order_approved_at,
        o.order_delivered_customer_date::TIMESTAMP as order_delivered_customer_date,
        o.order_estimated_delivery_date::TIMESTAMP as order_estimated_delivery_date,
        TO_CHAR(o.order_purchase_timestamp::TIMESTAMP, 'YYYYMMDD')::INT as date_id,
        i.price,
        i.freight_value,
        (i.price + i.freight_value) as total_value,
        NULL::VARCHAR(50) as marketing_channel,
        NULL::DECIMAL(10,2) as acquisition_cost,
        NULL::DECIMAL(10,2) as net_profit
    FROM public.raw_orders o 
    JOIN public.raw_order_items i ON o.order_id = i.order_id;
    """
    exec_sql(conn, q_fact_orders, "fact_orders")

    # Fact Payments (Grain: Transaction Level)
    q_fact_pay = """
    DROP TABLE IF EXISTS dwh.fact_payments;
    CREATE TABLE dwh.fact_payments AS
    SELECT 
        order_id,
        payment_sequential,
        payment_type,
        payment_installments,
        payment_value
    FROM public.raw_payments;
    """
    exec_sql(conn, q_fact_pay, "fact_payments")

    # Fact Reviews
    q_fact_rev = """
    DROP TABLE IF EXISTS dwh.fact_reviews;
    CREATE TABLE dwh.fact_reviews AS
    SELECT 
        review_id,
        order_id,
        review_score, 
        review_comment_title,
        REPLACE(review_comment_message, '\n', ' ') as review_comment_message,
        review_creation_date::TIMESTAMP as review_date
    FROM public.raw_reviews;
    """
    exec_sql(conn, q_fact_rev, "fact_reviews")

    # Creating Indexes
    print("\n   [Indexing]")
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_orders_date ON dwh.fact_orders(date_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_orders_seller ON dwh.fact_orders(seller_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_pay_order ON dwh.fact_payments(order_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_rev_order ON dwh.fact_reviews(order_id);"))
    print("    ✅ Indexes created.")

# -------------------------------------------------------
# 3. Time Dimension
# -------------------------------------------------------
print("\n   [Time Intelligence]")
try:
    date_range = pd.date_range(start='2016-01-01', end='2023-12-31')
    df_date = pd.DataFrame({'date': date_range})
    df_date['date_id'] = df_date['date'].dt.strftime('%Y%m%d').astype(int)
    df_date['year'] = df_date['date'].dt.year
    df_date['month'] = df_date['date'].dt.month
    df_date['quarter'] = df_date['date'].dt.quarter
    df_date['day_name'] = df_date['date'].dt.day_name()
    df_date['is_weekend'] = df_date['date'].dt.dayofweek.isin([5, 6])
    
    df_date.to_sql('dim_date', engine, schema='dwh', if_exists='replace', index=False)
    print("    ✅ dim_date created.")
except Exception as e:
    print(f"    ❌ Error generating dim_date: {e}")

print("\n🎉 PHASE 2 COMPLETE: Data Warehouse Ready.")