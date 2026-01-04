# 🛒 Olist Decision Engine

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-336791.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

> **A comprehensive Data Warehouse + Marketing Attribution Simulation Engine for E-commerce Analytics**

Advanced decision support system that simulates realistic marketing dynamics, calculates true customer acquisition costs (CAC), and identifies wasted marketing spend for the Olist Brazilian marketplace.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Data Pipeline](#-data-pipeline)
- [Simulation Engine](#-simulation-engine)
- [Output & Analysis](#-output--analysis)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

---

## 🎯 Overview

The Olist Decision Engine is a sophisticated data analytics platform designed for:

- **📊 Data Engineers**: Build production-grade ETL pipelines
- **🔬 Data Scientists**: Train ML models on realistic e-commerce data
- **💼 Business Analysts**: Analyze marketing ROI and customer behavior
- **🎓 Students**: Learn advanced analytics and attribution modeling

### What Makes It Unique?

- **🧠 Causal Marketing Simulation**: Not random data - physics-based marketing dynamics
- **💸 Waste Detection**: Identifies marketing spend that didn't convert to sales
- **🎮 Difficulty Levels**: Easy, Medium, Hard scenarios for progressive learning
- **🔗 Attribution Bridge**: Connects marketing activity to actual orders using inventory logic
- **📈 Real Business Metrics**: Commission rates, logistics costs, SLA penalties

---

## ✨ Key Features

### 1. **Multi-Channel Marketing Simulation**
- Facebook Ads, Google Search, Instagram Influencers, Email, Organic SEO
- AdStock modeling (memory effect)
- Saturation curves (diminishing returns)
- Seasonality patterns (Black Friday, Christmas)

### 2. **Advanced Attribution Engine**
- Stateful inventory system
- 3-day lookback window
- Weighted attribution with decay
- Organic vs. Paid classification

### 3. **Financial Analytics**
- Unit-level economics (per order item)
- Daily P&L statements
- Marketing waste calculation
- SaaS subscription revenue modeling

### 4. **ML-Enhanced Data Quality**
- Random Forest for missing product weights
- Category classification for unknown products
- Sentiment analysis on customer reviews
- NMF topic modeling for satisfaction reasons

### 5. **Interactive Training Mode**
- GUI launcher with 3 difficulty levels
- Configurable data quality (Clean/Messy/Nightmare)
- Dual-output system (training + production)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAW DATA (CSV Files)                      │
│     Orders, Products, Customers, Sellers, Reviews, etc.      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              PHASE 1: Infrastructure Setup                   │
│  • Create PostgreSQL Database                                │
│  • Load CSV → Raw Tables (public schema)                     │
│  • Generate JSON artifacts                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              PHASE 2: Data Warehouse Build                   │
│  • Create DWH schema                                         │
│  • Build Dimensions: Products, Customers, Sellers, Date      │
│  • Build Facts: Orders, Payments, Reviews                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         PHASE 3: Marketing Engine (Simulation)               │
│  • Generate daily marketing spend                            │
│  • Calculate impressions & clicks                            │
│  • Apply AdStock & saturation                                │
│  • Output: fact_marketing_daily                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         PHASE 4: Attribution Bridge                          │
│  • Match orders to marketing clicks                          │
│  • Apply decay & weighted allocation                         │
│  • Calculate CAC per order                                   │
│  • Update: fact_orders.marketing_channel                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         PHASE 5: Unified Financials                          │
│  • Calculate commission revenue                              │
│  • Compute logistics margins                                 │
│  • Identify marketing waste                                  │
│  • Output: fact_financials, fact_daily_pnl                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│      NOTEBOOK: Preprocess Static Dimensions (ML)             │
│  • Impute missing product weights (Random Forest)            │
│  • Classify unknown categories (Random Forest)               │
│  • Calculate satisfaction scores (Sentiment Analysis)        │
│  • Extract satisfaction reasons (NMF Topic Modeling)         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              READY FOR ANALYSIS & DASHBOARDS                 │
│         dwh(ready_to_be_analyzed)/ folder + Database         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Installation

### Prerequisites

- **Python 3.8+**
- **PostgreSQL 13+**
- **Git**

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/olist-decision-engine.git
cd olist-decision-engine
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
```
pandas>=1.5.0
numpy>=1.23.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
matplotlib>=3.6.0
seaborn>=0.12.0
scikit-learn>=1.2.0
nltk>=3.8.0
jupyter>=1.0.0
nbconvert>=7.0.0
```

### Step 4: Download NLTK Data

```python
import nltk
nltk.download('vader_lexicon')
```

### Step 5: Setup PostgreSQL

```bash
# Install PostgreSQL (if not installed)
# Windows: Download from postgresql.org
# macOS: brew install postgresql
# Linux: sudo apt-get install postgresql

# Create Database User
createuser -U postgres -P postgres  # Set password: postgres

# The pipeline will auto-create the database
```

### Step 6: Prepare Data

Place Olist CSV files in `data/` folder:
- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_customers_dataset.csv`
- `olist_sellers_dataset.csv`
- `olist_products_dataset.csv`
- `olist_geolocation_dataset.csv`
- `product_category_name_translation.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`

**Download from**: [Kaggle - Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

---

## 🚀 Quick Start

### Option 1: Full Pipeline (Recommended for First Run)

```bash
python run_pipeline.py
```

This will:
1. ✅ Create database `olist_engine_db`
2. ✅ Load all raw data
3. ✅ Build Data Warehouse
4. ✅ Simulate marketing activity
5. ✅ Calculate attribution
6. ✅ Generate financial reports
7. ✅ Run preprocessing notebook

**Expected Duration**: 5-10 minutes

### Option 2: Training Mode (Interactive GUI)

```bash
python training_gui.py
```

**Features:**
- Select scenario name
- Choose **Market Difficulty**: Easy / Medium / Hard
- Choose **Data Quality**: Clean / Messy / Nightmare
- Click "Initialize Master Engine"

**Output**: `Training_Output/{ScenarioName}/` folder with CSV files

### Option 3: Manual Training Engine

```python
from training_engine import OlistMasterEngineV5

sim = OlistMasterEngineV5(difficulty="Hard", output_folder="MyScenario")
sim.load_context()
sim.simulate_marketing()
sim.run_attribution_engine()
sim.calculate_financials()
sim.export()
```

---

## 📁 Project Structure

```
olist-decision-engine/
│
├── 📂 data/                          # Raw CSV files (user-provided)
│   ├── olist_orders_dataset.csv
│   ├── olist_products_dataset.csv
│   └── ...
│
├── 📂 pipeline/                      # ETL Scripts (Sequential)
│   ├── 01_setup_infrastructure.py    # Database creation + data loading
│   ├── 02_build_dwh_schema.py        # DWH schema construction
│   ├── 03_market_engine.py           # Marketing simulation
│   ├── 04_attribution_bridge.py      # Attribution logic
│   └── 05_unified_financials.py      # Financial calculations
│
├── 📂 notebooks/                     # Jupyter Notebooks
│   └── 01_Preprocess_Static_Dimensions.ipynb
│
├── 📂 json_source/                   # Generated JSON artifacts
│   └── products.json
│
├── 📂 Training_Output/               # Training simulation outputs
│   └── {ScenarioName}_M-{Diff}_D-{Quality}/
│       ├── fact_marketing_daily.csv
│       └── fact_financials.csv
│
├── 📂 dwh(ready_to_be_analyzed)/    # Production-ready CSVs
│   ├── dim_products.csv
│   ├── dim_customers.csv
│   ├── dim_sellers.csv
│   ├── dim_date.csv
│   ├── fact_marketing_daily.csv
│   ├── fact_financials.csv
│   └── fact_reviews.csv
│
├── 📄 db_config.py                   # Database configuration
├── 📄 run_pipeline.py                # Pipeline orchestrator
├── 📄 training_engine.py             # Simulation engine
├── 📄 training_gui.py                # GUI launcher
├── 📄 requirements.txt               # Python dependencies
└── 📄 README.md                      # This file
```

---

## 🔄 Data Pipeline

### Pipeline Scripts (Sequential Execution)

#### **01_setup_infrastructure.py**
- Creates PostgreSQL database
- Loads 9 CSV files → `public` schema
- Generates JSON artifacts

**Output Tables:**
- `public.raw_orders`
- `public.raw_order_items`
- `public.raw_customers`
- `public.raw_sellers`
- `public.raw_products`
- `public.raw_geolocation`
- `public.raw_category_translation`
- `public.raw_payments`
- `public.raw_reviews`

---

#### **02_build_dwh_schema.py**
Creates normalized Data Warehouse in `dwh` schema.

**Dimensions:**
| Table | Description | Key Columns |
|-------|-------------|-------------|
| `dim_products` | Product catalog | product_id, category, weight |
| `dim_sellers` | Seller profiles | seller_id, state, city |
| `dim_customers` | Customer locations | customer_id, state, city |
| `dim_date` | Calendar (2016-2023) | date_id, year, month, is_weekend |

**Facts:**
| Table | Grain | Description |
|-------|-------|-------------|
| `fact_orders` | Order Item | Core transactional data |
| `fact_payments` | Payment Transaction | Payment methods & installments |
| `fact_reviews` | Review | Customer ratings & comments |

---

#### **03_market_engine.py**
**Marketing Simulation with Causal Physics**

**Channels Simulated:**
```python
{
    'Facebook_Ads': {
        'base_daily_budget': 85,
        'cpm': 12.5,
        'base_ctr': 0.009
    },
    'Google_Search': {
        'base_daily_budget': 120,
        'cpm': 28.0,
        'base_ctr': 0.028
    },
    'Influencer_Instagram': {...},
    'Email_Marketing': {...},
    'Organic_SEO': {...}
}
```

**Key Calculations:**

1. **Spend Generation**:
   ```
   Daily Spend = Base Budget × Seasonality × Noise
   ```

2. **Impressions**:
   ```
   Impressions = (Spend / CPM) × 1000
   ```

3. **AdStock (Memory Effect)**:
   ```
   AdStock_t = α × Impressions_t + (1-α) × AdStock_{t-1}
   ```

4. **Saturation Curve**:
   ```
   Efficiency = 1 / (1 + (AdStock / Capacity)^1.5)
   ```

5. **Clicks**:
   ```
   Clicks = AdStock × CTR × Efficiency × Noise
   ```

**Output**: `dwh.fact_marketing_daily` (5 channels × ~600 days = 3,000 rows)

---

#### **04_attribution_bridge.py**
**The Attribution Engine - Core Innovation**

**Problem Statement:**
> "We spent $10,000 on marketing. Which orders came from ads vs. organic?"

**Solution - Inventory-Based Attribution:**

```python
# Daily Pool (3-Day Lookback with Decay)
pool = {
    'Facebook': 1000 clicks (weight: 1.0, 0.5, 0.33),
    'Google': 500 clicks,
    ...
}

# For each order on Day X:
if pool.has_clicks():
    channel = weighted_random_choice(pool)
    pool[channel] -= 1  # Consume inventory
else:
    channel = 'Direct/Organic'
```

**Key Features:**
- **Stateful**: Clicks persist across days with decay
- **Realistic**: Limited supply → scarcity → organic fallback
- **Weighted**: Channels with more clicks get more orders

**Output**: Updates `fact_orders.marketing_channel` + `acquisition_cost`

---

#### **05_unified_financials.py**
**Complete Financial Model**

**Revenue Streams:**
1. **Commission Revenue**:
   ```
   Commission = Price × Commission_Rate
   # Rates: 10% (Enterprise), 15% (Standard), 20% (New)
   ```

2. **Logistics Margin**:
   ```
   Logistics Margin = Freight_Value - (Freight_Value × 1.10)
   # Olist charges customer freight, pays carrier 110% of that
   ```

3. **SaaS Subscriptions**:
   ```python
   if monthly_gmv > 10000: tier = 'Enterprise' ($999.90)
   elif monthly_gmv > 2000: tier = 'Pro' ($199.90)
   else: tier = 'Basic' ($49.90)
   ```

**Cost Structure:**
1. **CAC (Customer Acquisition Cost)**:
   ```
   Unit CAC = Channel_Daily_Spend / Orders_Attributed
   ```

2. **Operational Costs**:
   ```
   Ops Cost = Base_Cost + (Items_Count × Item_Cost) × Weekend_Tax
   ```

3. **SLA Penalties**:
   ```
   if actual_delivery > estimated + 2_days:
       penalty = freight_value × 0.5
   ```

**Critical Innovation - Marketing Waste:**
```python
Total Marketing Spend = $10,000 (actual cash out)
Attributed CAC = $6,500 (linked to orders)
Marketing Waste = $3,500 (clicks that bounced/didn't convert)
```

**Output Tables:**
- `fact_financials` (item-level economics)
- `fact_daily_pnl` (daily P&L with waste)
- `fact_seller_subscriptions` (SaaS revenue)

---

### Notebook: ML Preprocessing

**Jupyter Notebook**: `01_Preprocess_Static_Dimensions.ipynb`

**Tasks:**

1. **Impute Missing Product Weights**:
   ```python
   Random Forest Regressor
   Input: volume_cm3, category_encoded
   Output: predicted_weight_g
   ```

2. **Classify Unknown Categories**:
   ```python
   Random Forest Classifier
   Input: weight, volume
   Output: predicted_category
   Result: 610 products reclassified
   ```

3. **Sentiment Analysis**:
   ```python
   Hybrid Score = 0.5 × Stars + 0.5 × NLTK_Sentiment
   Normalized: 0-100 scale, mean=50, std=15
   ```

4. **Topic Modeling (NMF)**:
   ```python
   Input: Portuguese review text
   Output: English reason labels
   - "Delivery Delay / Issues"
   - "Product Quality / Defect"
   - "Fast / On-time Delivery"
   - "Good Product Quality"
   - etc.
   ```

**Output**: Updates `dim_products` and `fact_reviews` in DWH

---

## 🎮 Simulation Engine

### Difficulty Levels

| Level | Spend Multiplier | Efficiency | Burn Rate | Organic Traffic | Data Chaos |
|-------|------------------|------------|-----------|-----------------|------------|
| **Easy** | 1.0x | 100% | 20% | 30% | 0% |
| **Medium** | 1.5x | 100% | 30% | 20% | 5% |
| **Hard** | 2.5x | 50% | 40% | 10% | 20% |

### Business Physics Parameters

```python
params = {
    'spend_mult': 2.5,        # Marketing budget multiplier
    'ad_eff': 0.5,            # Channel efficiency (lower = more waste)
    'base_burn': 0.4,         # Funnel loss rate (40% bounce)
    'org_base': 0.10,         # Organic traffic baseline
    'chaos_level': 0.30,      # Data quality issues
    'missing_data_prob': 0.10, # API failure rate
    'ops_base': 3.5,          # Base operational cost
    'ops_item': 1.0,          # Per-item handling cost
    'weekend_tax': 1.5,       # Weekend labor premium
    'freight_markup': 1.6     # Carrier cost multiplier
}
```

### Decoupling Architecture

**GUI allows independent control:**
- **Market Physics** (Easy/Medium/Hard) → `spend_mult`, `ad_eff`, `base_burn`
- **Data Quality** (Clean/Messy/Nightmare) → `chaos_level`, `missing_data_prob`

**Example Use Case:**
> "Train ML model on Hard market conditions, but Clean data"
> 
> → Set Market=Hard, Data=Clean

---

## 📊 Output & Analysis

### Database Tables (dwh schema)

**Key Tables for Analysis:**

```sql
-- Daily P&L with Marketing Waste
SELECT 
    date_id,
    total_marketing_spend,        -- Total cash out
    acquisition_cost,              -- CAC linked to orders
    marketing_waste,               -- Unconverted spend
    net_profit_loss                -- Bottom line
FROM dwh.fact_daily_pnl
ORDER BY date_id;

-- Order-Level Economics
SELECT 
    order_id,
    marketing_channel,
    price,
    acquisition_cost,
    commission_revenue,
    net_contribution              -- Unit profit
FROM dwh.fact_financials;

-- Marketing Performance
SELECT 
    channel,
    SUM(spend) as total_spend,
    SUM(clicks) as total_clicks,
    AVG(effective_ctr) as avg_ctr
FROM dwh.fact_marketing_daily
GROUP BY channel;
```

### CSV Exports

**Location**: `dwh(ready_to_be_analyzed)/`

**Files:**
- `dim_products.csv` (32,951 products)
- `dim_customers.csv` (99,441 customers)
- `dim_sellers.csv` (3,095 sellers)
- `dim_date.csv` (2016-2023 calendar)
- `fact_marketing_daily.csv` (~3,000 rows)
- `fact_financials.csv` (~112,000 items)
- `fact_reviews.csv` (with satisfaction scores)

**Usage:**
```python
import pandas as pd

# Load data
df_pnl = pd.read_csv('dwh(ready_to_be_analyzed)/fact_daily_pnl.csv')
df_fin = pd.read_csv('dwh(ready_to_be_analyzed)/fact_financials.csv')

# Analyze marketing waste
waste_by_month = df_pnl.groupby(df_pnl['date_id'].astype(str).str[:6])[
    ['total_marketing_spend', 'marketing_waste']
].sum()

waste_by_month['waste_pct'] = (
    waste_by_month['marketing_waste'] / 
    waste_by_month['total_marketing_spend'] * 100
)

print(waste_by_month)
```

---

## ⚙️ Configuration

### Database Settings

**File**: `db_config.py`

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "postgres",
    "pass": "postgres",
    "db": "olist_engine_db"
}
```

**To Use Remote Database:**
```python
DB_CONFIG = {
    "host": "your-server.com",
    "user": "your_username",
    "pass": "your_password",
    "db": "olist_engine_db"
}
```

### Pipeline Configuration

**File**: `run_pipeline.py`

```python
PIPELINE = [
    "01_setup_infrastructure.py",
    "02_build_dwh_schema.py",
    "03_market_engine.py",
    "04_attribution_bridge.py",
    "05_unified_financials.py"
]

# Add/remove scripts as needed
```

### Simulation Seeds

```python
# training_engine.py
SEEDS = {
    'Easy': 101,
    'Medium': 202,
    'Hard': 404
}

# For reproducible results, set:
np.random.seed(SEEDS[difficulty])
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. **Database Connection Failed**
```
Error: could not connect to server: Connection refused
```

**Solution:**
```bash
# Check PostgreSQL is running
# Windows
pg_ctl status

# macOS/Linux
sudo systemctl status postgresql

# Start if stopped
sudo systemctl start postgresql
```

#### 2. **Module Not Found: psycopg2**
```
ModuleNotFoundError: No module named 'psycopg2'
```

**Solution:**
```bash
pip install psycopg2-binary
```

#### 3. **CSV Files Not Found**
```
FileNotFoundError: data/olist_orders_dataset.csv
```

**Solution:**
- Download Olist dataset from Kaggle
- Extract all CSV files to `data/` folder
- Verify file names match exactly (case-sensitive)

#### 4. **Notebook Execution Failed**
```
ERROR: Notebook path '...' not found
```

**Solution:**
```bash
# Install Jupyter & nbconvert
pip install jupyter nbconvert

# Run notebook manually
jupyter notebook notebooks/01_Preprocess_Static_Dimensions.ipynb
```

#### 5. **Memory Error on Large Dataset**
```
MemoryError: Unable to allocate array
```

**Solution:**
```python
# In script, use chunking:
for chunk in pd.read_csv(file, chunksize=10000):
    chunk.to_sql(table, engine, if_exists='append')
```

#### 6. **NLTK Data Not Found**
```
LookupError: Resource vader_lexicon not found
```

**Solution:**
```python
import nltk
nltk.download('vader_lexicon')
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

### Development Setup

```bash
# Fork & clone
git clone https://github.com/yourusername/olist-decision-engine.git
cd olist-decision-engine

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes & commit
git commit -m "Add: Your feature description"

# Push & create PR
git push origin feature/your-feature-name
```

### Code Style

- Follow PEP 8 for Python code
- Use docstrings for functions
- Add type hints where possible
- Comment complex logic

### Testing

```bash
# Run pipeline test
python run_pipeline.py

# Verify output
ls dwh(ready_to_be_analyzed)/
```

---

## 📚 Additional Resources

### Learning Materials

- **Attribution Modeling**: [Google Analytics Attribution](https://support.google.com/analytics/answer/1662518)
- **AdStock Theory**: [Marketing Science Paper](https://doi.org/10.1287/mksc.1080.0361)
- **NMF Topic Modeling**: [Scikit-learn Guide](https://scikit-learn.org/stable/modules/decomposition.html#nmf)

### Olist Dataset

- **Kaggle**: [Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- **Schema Documentation**: [Olist GitHub](https://github.com/olistbr/work-at-olist-data)

### Related Projects

- **LightFM**: Hybrid recommendation systems
- **CausalImpact**: Bayesian causal inference (Google)
- **Prophet**: Time series forecasting (Facebook)

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 👤 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your LinkedIn](https://linkedin.com/in/yourprofile)
- Email: your.email@example.com

---

## 🙏 Acknowledgments

- **Olist** for providing the public dataset
- **Kaggle** community for insights
- **SQLAlchemy** & **Pandas** teams for excellent tools

---

## 📈 Project Status

- ✅ Core pipeline complete
- ✅ Attribution engine validated
- ✅ ML preprocessing implemented
- 🚧 Dashboard (Tableau/PowerBI) - In Progress
- 📝 API endpoint - Planned

---

## 💡 Use Cases

### For Students
- Learn ETL pipeline design
- Practice SQL & Pandas
- Understand attribution modeling
- Train ML models on realistic data

### For Data Engineers
- Reference architecture for DWH
- Simulation engine patterns
- Batch processing optimization

### For Analysts
- Marketing ROI analysis
- Customer segmentation
- Product performance analysis
- Waste identification

### For Researchers
- Test attribution algorithms
- Causal inference studies
- Marketing mix modeling

---

## 🎓 Key Learnings

After completing this project, you will understand:

1. **ETL Design Patterns**
   - Dimensional modeling (star schema)
   - Slowly changing dimensions
   - Incremental loading

2. **Marketing Science**
   - Attribution modeling
   - AdStock & carryover effects
   - Saturation curves
   - Multi-touch attribution

3. **Financial Analytics**
   - Unit economics
   - Contribution margin
   - CAC calculation
   - Waste identification

4. **Machine Learning**
   - Imputation with Random Forest
   - NMF topic modeling
   - Sentiment analysis
   - Feature engineering

---

## 📞 Support

### Get Help

- **Issues**: [GitHub Issues](https://github.com/yourusername/olist-decision-engine/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/olist-decision-engine/discussions)
- **Email**: support@yourproject.com

### FAQ

**Q: How long does the full pipeline take?**
A: 5-10 minutes on average hardware (depends on data size)

**Q: Can I use a different database?**
A: Yes, modify `db_config.py` to use MySQL/SQLite (may need SQL syntax adjustments)

**Q: How do I add a new marketing channel?**
A: Edit `channels_config` in `03_market_engine.py` and add your channel parameters

**Q: Can I integrate my own data?**
A: Yes, replace CSV files in `data/` folder (match schema structure)

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with ❤️ for the data community

</div>
