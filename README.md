# Enterprise Retail Intelligence & Decision Engine

[![Python](https://img.shields.io/badge/Python-3.14-blue)](https://python.org)
[![MySQL](https://img.shields.io/badge/MySQL-8.4-orange)](https://mysql.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.64-red)](https://streamlit.io)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.9-green)](https://scikit-learn.org)
[![Dataset](https://img.shields.io/badge/Dataset-Instacart%202017-lightgrey)](https://www.kaggle.com/c/instacart-market-basket-analysis)

> **A complete, production-quality retail analytics portfolio project** demonstrating end-to-end data engineering, SQL analytics, machine learning, and business intelligence on 37M+ real transaction records.

---

## 1. Project Overview

This project builds a full analytical platform on the Instacart Market Basket Analysis dataset (2017). It demonstrates the complete analytics engineering lifecycle:

- **Data Engineering** — profiling, cleaning, validation, MySQL loading
- **SQL Analytics** — 47 business queries covering customer, product, time, and reorder analysis  
- **Python EDA** — exploratory analysis across 9 Jupyter notebooks
- **Customer Analytics** — behavioral feature engineering and K-Means segmentation
- **Machine Learning** — reorder prediction with Logistic Regression and Random Forest (leakage-free)
- **Market Basket Analysis** — product association rules on 32M+ transactions
- **Business Intelligence** — Power BI dashboard documentation (7 pages)
- **Streamlit Application** — interactive decision engine with What-If analysis

---

## 2. Business Problem

Retail businesses need to understand:
- Which customers are most valuable and what drives their behavior?
- Which products are staples vs one-time purchases?
- When do customers shop and what does that mean for operations?
- Which products are frequently bought together (cross-sell opportunities)?
- Can we predict whether a customer will reorder a product?

This project provides SQL, Python, and interactive Streamlit answers to all of these questions using publicly available behavioral data.

---

## 3. Dataset

**Source:** [Instacart Market Basket Analysis](https://www.kaggle.com/c/instacart-market-basket-analysis) (Kaggle 2017)

| File | Rows | Size |
|------|------|------|
| orders.csv | 3,421,083 | 104 MB |
| order_products__prior.csv | 32,434,489 | 551 MB |
| order_products__train.csv | 1,384,617 | 24 MB |
| products.csv | 49,688 | 2.1 MB |
| aisles.csv | 134 | 2.5 KB |
| departments.csv | 21 | 270 B |

**Total:** ~682 MB raw, 37.3M rows

**What the data contains:**
- 206,209 unique customers
- 3.4M grocery orders
- 49,688 unique products across 21 departments and 134 aisles
- Day of week, hour of day, and days since prior order for each order
- Whether each product was a reorder or first purchase

**What the data does NOT contain** (and this project never fabricates):
- Revenue, price, or profit data
- Customer demographics
- Geographic information
- Inventory levels

---

## 4. Architecture

```
Raw CSV (682 MB)
     ↓
Phase 2: Data Profiling        → reports/data_profile.md
     ↓
Phase 4: Data Cleaning         → data/Processed/*.parquet
     ↓
Phase 5: Data Validation       → reports/validation_report.md (70/70 PASS)
     ↓
Phase 6: MySQL 8.4             → enterprise_bi database (37M rows)
     ↓
Phase 7: SQL Analytics         → 47 queries across 4 SQL files
     ↓
Phase 8: Python EDA            → notebooks/ (9 notebooks)
     ↓
Phase 9: Customer Features     → customer_features.parquet (17 features)
     ↓
Phase 10: Segmentation         → customer_segments.parquet (K-Means)
     ↓
Phase 11: Reorder Prediction   → Random Forest + Logistic Regression
     ↓
Phase 12: Market Basket        → market_basket_results.parquet
     ↓
Power BI Dashboard             → 7 pages (documented in powerbi/)
     ↓
Streamlit App                  → streamlit/app.py
```

---

## 5. Technology Stack

| Category | Technology | Version |
|----------|-----------|---------|
| Language | Python | 3.14.6 |
| Data Manipulation | Pandas | 3.0.5 |
| Numerical Computing | NumPy | 2.5.3 |
| Visualization | Matplotlib, Seaborn | 3.11.2, 0.13.2 |
| Machine Learning | scikit-learn | 1.9.1 |
| Database | MySQL | 8.4.11 |
| DB Connector | SQLAlchemy + PyMySQL | 2.0.54, 1.2.0 |
| Columnar Storage | Apache Parquet (PyArrow) | 25.0.1 |
| Web Application | Streamlit | 1.64.0 |
| Notebooks | JupyterLab | 4.6.3 |
| BI Tool | Power BI Desktop | (documented) |
| Version Control | Git + GitHub | — |

---

## 6. Project Structure

```
enterprise-business-intelligence/
│
├── data/
│   ├── Raw/                        ← Source CSVs (never modified)
│   └── Processed/                  ← Cleaned Parquet files + ML outputs
│
├── python/
│   ├── profile_dataset.py          ← Phase 2: Profiling
│   ├── clean_data.py               ← Phase 4: Cleaning
│   ├── validate_data.py            ← Phase 5: Validation (70 checks)
│   ├── load_mysql.py               ← Phase 6: MySQL bulk loader
│   ├── customer_features.py        ← Phase 9: Feature engineering
│   ├── customer_segmentation.py    ← Phase 10: K-Means segmentation
│   ├── reorder_prediction.py       ← Phase 11: ML reorder prediction
│   ├── market_basket.py            ← Phase 12: Association analysis
│   └── run_pipeline.py             ← Master pipeline runner
│
├── sql/
│   ├── 01_create_database.sql
│   ├── 02_create_tables.sql        ← 6 staging tables
│   ├── 03_indexes.sql              ← 12 analytical indexes
│   ├── 04_load_validation.sql
│   ├── 05_business_queries.sql     ← Customer + product + dept queries
│   ├── 06_advanced_analytics.sql   ← Window functions, CTEs, cohorts
│   ├── 07_views.sql                ← 6 analytical views
│   └── 08_business_questions.sql   ← 35 business questions answered
│
├── notebooks/                      ← 9 Jupyter EDA notebooks
├── streamlit/                      ← Streamlit decision engine
├── powerbi/                        ← Power BI documentation
│
├── reports/
│   ├── project_audit.md
│   ├── data_profile.md
│   ├── data_quality_report.md
│   ├── data_dictionary.md
│   ├── data_cleaning_log.md
│   ├── validation_report.md
│   ├── database_design.md
│   ├── customer_segments.md
│   ├── model_evaluation.md
│   ├── market_basket_insights.md
│   └── final_project_report.md
│
├── logs/                           ← Pipeline execution logs
├── .env.example                    ← Credential template (no real values)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 7. Installation

### Prerequisites
- Python 3.12+ with pip
- MySQL 8.4 running locally
- Git

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/harshit-aiot/enterprise-retail-intelligence.git
cd enterprise-retail-intelligence

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure database credentials
cp .env.example .env
# Edit .env with your MySQL password

# 5. Download the Instacart dataset
# Place the 6 CSV files in data/Raw/
# Download from: https://www.kaggle.com/c/instacart-market-basket-analysis
```

---

## 8. Running the Pipeline

```bash
# Activate environment
source .venv/bin/activate

# Run full pipeline (all phases)
python python/run_pipeline.py

# Or run individual phases
python python/run_pipeline.py --phase profile
python python/run_pipeline.py --phase clean
python python/run_pipeline.py --phase validate
python python/run_pipeline.py --phase load_db
python python/run_pipeline.py --phase features
python python/run_pipeline.py --phase segment
python python/run_pipeline.py --phase predict
python python/run_pipeline.py --phase basket
```

---

## 9. Running the Streamlit App

```bash
source .venv/bin/activate
cd streamlit
streamlit run app.py
```

Open: http://localhost:8501

---

## 10. MySQL Setup

```bash
# The pipeline creates the database automatically
# Alternatively run SQL scripts manually:
mysql -u root -p < sql/01_create_database.sql
mysql -u root -p enterprise_bi < sql/02_create_tables.sql
mysql -u root -p enterprise_bi < sql/03_indexes.sql

# Then load data via Python:
python python/load_mysql.py

# Validate load:
mysql -u root -p enterprise_bi < sql/04_load_validation.sql
```

---

## 11. Key Findings (From Actual Data)

> All findings are based on real calculations — no fabricated metrics.

| Finding | Evidence |
|---------|----------|
| Overall reorder rate: **58.97%** | AVG(reordered) on 32.4M prior rows |
| Average basket size: **10.09 products/order** | COUNT/order on prior transactions |
| 206,209 unique customers | COUNT(DISTINCT user_id) |
| Saturday + Sunday = highest order days | Verified via order_dow distribution |
| Peak order hour: 10am | order_hour_of_day distribution |
| Produce is #1 department by volume | GROUP BY department_id |

---

## 12. Limitations

- No revenue, price, or profit data — value-based analysis is not possible
- No customer demographics — segmentation is behavioral only  
- No actual timestamps — only day-of-week and hour-of-day
- Dataset from 2017 — market basket patterns may have changed
- Reorder prediction uses classification metrics — does not predict timing or quantity

---

## 13. Author

**Harshit**  
Data Analyst & Analytics Engineer  
GitHub: [@harshit-aiot](https://github.com/harshit-aiot)

---

*This is a portfolio project built on the Instacart Market Basket Analysis public dataset.*
