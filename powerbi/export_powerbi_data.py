"""
export_powerbi_data.py
======================
Enterprise Retail Intelligence & Decision Engine
Phase 14: Power BI Data Exporter

Exports clean Star-Schema CSV files into `powerbi/data/` for direct
drag-and-drop import into Power BI Desktop.
"""

import os
from pathlib import Path
import pandas as pd

BASE_DIR = Path("/Volumes/Harshit Drive/enterprise-business-intelligence")
PROCESSED_DIR = BASE_DIR / "data" / "Processed"
OUTPUT_DIR = BASE_DIR / "powerbi" / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Starting Power BI Data Export...")

# 1. Dimensions
df_depts = pd.read_parquet(PROCESSED_DIR / "departments_clean.parquet")
df_depts.to_csv(OUTPUT_DIR / "dim_departments.csv", index=False)
print("  -> Exported dim_departments.csv")

df_aisles = pd.read_parquet(PROCESSED_DIR / "aisles_clean.parquet")
df_aisles.to_csv(OUTPUT_DIR / "dim_aisles.csv", index=False)
print("  -> Exported dim_aisles.csv")

df_prods = pd.read_parquet(PROCESSED_DIR / "products_clean.parquet")
df_prods.to_csv(OUTPUT_DIR / "dim_products.csv", index=False)
print("  -> Exported dim_products.csv")

# Time Dimension (24 hours)
hours = list(range(24))
time_data = []
for h in hours:
    if 6 <= h < 12:
        bucket = "Morning"
    elif 12 <= h < 17:
        bucket = "Afternoon"
    elif 17 <= h < 21:
        bucket = "Evening"
    else:
        bucket = "Night"
    peak = "Yes" if 10 <= h <= 16 else "No"
    time_data.append({"hour_of_day": h, "time_bucket": bucket, "peak_window": peak})
pd.DataFrame(time_data).to_csv(OUTPUT_DIR / "dim_time.csv", index=False)
print("  -> Exported dim_time.csv")

# 2. Customer Dimension with Segments
df_cust = pd.read_parquet(PROCESSED_DIR / "customer_segments.parquet")
# Export a sample of 25,000 customers for rapid Power BI loading
df_cust.sample(n=min(25000, len(df_cust)), random_state=42).to_csv(OUTPUT_DIR / "dim_customers_sample.csv", index=False)
print("  -> Exported dim_customers_sample.csv (25,000 sampled profiles)")

# 3. Market Basket Rules
df_rules = pd.read_parquet(PROCESSED_DIR / "market_basket_results.parquet")
df_rules.to_csv(OUTPUT_DIR / "fact_market_basket.csv", index=False)
print("  -> Exported fact_market_basket.csv")

# 4. Train Order Items (1.38M rows - perfect size for Power BI Desktop in-memory engine)
df_train = pd.read_parquet(PROCESSED_DIR / "order_products_train_clean.parquet")
df_train.to_csv(OUTPUT_DIR / "fact_order_items_train.csv", index=False)
print(f"  -> Exported fact_order_items_train.csv ({len(df_train):,} rows)")

# 5. Orders Header (Filtered to train order IDs)
df_orders = pd.read_parquet(PROCESSED_DIR / "orders_clean.parquet")
train_order_ids = set(df_train['order_id'].unique())
df_orders_train = df_orders[df_orders['order_id'].isin(train_order_ids)]
df_orders_train.to_csv(OUTPUT_DIR / "fact_orders_train.csv", index=False)
print(f"  -> Exported fact_orders_train.csv ({len(df_orders_train):,} headers)")

# 6. Aggregated Operational Heatmap (All 3.42M orders aggregated by DOW and Hour)
dow_hour_agg = df_orders.groupby(['order_dow', 'order_hour_of_day']).agg(
    order_volume=('order_id', 'count')
).reset_index()
dow_names = {0: 'Sunday', 1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
dow_hour_agg['day_name'] = dow_hour_agg['order_dow'].map(dow_names)
dow_hour_agg.to_csv(OUTPUT_DIR / "agg_dow_hour_heatmap.csv", index=False)
print("  -> Exported agg_dow_hour_heatmap.csv")

print("\n✅ Power BI Star-Schema CSV files exported successfully!")
