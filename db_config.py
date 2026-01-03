from sqlalchemy import create_engine

# ==========================================
# 🏠 LOCAL SETTINGS
# ==========================================
DB_CONFIG = {
    "host": "localhost",
    "user": "postgres",
    "pass": "postgres",       
    "db":   "olist_engine_db" 
}

# ==========================================
#  ENGINE BUILDER
# ==========================================
print(f"🏠 CONNECTING TO LOCAL DB: {DB_CONFIG['db']}")

db_url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['pass']}@{DB_CONFIG['host']}:5432/{DB_CONFIG['db']}"

engine = create_engine(db_url)

def get_engine():
    return engine