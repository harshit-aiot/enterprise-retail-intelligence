"""
customer_features.py
====================
Enterprise Retail Intelligence & Decision Engine
Phase 9: Customer Analytics

Builds a comprehensive per-customer behavioral feature table
from the cleaned Parquet data.

Features built (all from actual data — no fabrication):
    user_id
    total_orders           — total number of orders placed
    avg_order_size         — average products per order
    total_products         — total product line items in prior orders
    unique_products        — unique products ever purchased
    reorder_count          — number of reordered items
    reorder_rate           — fraction of items that are reorders
    avg_days_between_orders
    std_days_between_orders
    min_days_between_orders
    max_days_between_orders
    preferred_order_dow    — most common day of week
    preferred_order_hour   — most common hour
    unique_departments     — number of distinct departments shopped
    unique_aisles          — number of distinct aisles shopped
    product_diversity      — unique_products / total_products (novelty rate)
    avg_cart_position      — average add_to_cart_order (lower = more habitual)

Output:
    data/Processed/customer_features.parquet

Usage:
    python python/customer_features.py
"""

import sys
import logging
import time
from pathlib import Path

import pandas as pd
import numpy as np

# ─── Logging ───────────────────────────────────────────────────────────────────
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "customer_features.log", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

PROJECT_ROOT  = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "Processed"


def build_customer_features() -> pd.DataFrame:
    """
    Build the customer feature table from cleaned Parquet files.

    Strategy:
    - Load orders + prior order-products + products
    - Aggregate to user-level features
    - All operations are vectorized Pandas — no Python loops
    """
    logger.info("Loading cleaned data ...")
    t0 = time.time()

    orders = pd.read_parquet(PROCESSED_DIR / "orders_clean.parquet")
    prior  = pd.read_parquet(PROCESSED_DIR / "order_products_prior_clean.parquet")
    prods  = pd.read_parquet(PROCESSED_DIR / "products_clean.parquet",
                             columns=["product_id", "aisle_id", "department_id"])

    logger.info(f"  Orders:  {len(orders):,} rows")
    logger.info(f"  Prior:   {len(prior):,} rows")
    logger.info(f"  Loaded in {time.time()-t0:.1f}s")

    # Keep only prior orders for behavioral features
    prior_orders = orders[orders["eval_set"] == "prior"].copy()
    logger.info(f"  Prior-set orders: {len(prior_orders):,}")

    # ── Feature 1: Order-level stats from orders table ─────────────────────────
    logger.info("\nBuilding order-level features ...")

    order_stats = prior_orders.groupby("user_id").agg(
        total_orders          = ("order_id",                  "count"),
        avg_days_between_orders = ("days_since_prior_order",  "mean"),
        std_days_between_orders = ("days_since_prior_order",  "std"),
        min_days_between_orders = ("days_since_prior_order",  "min"),
        max_days_between_orders = ("days_since_prior_order",  "max"),
    ).reset_index()

    # Round day stats
    for col in ["avg_days_between_orders", "std_days_between_orders",
                "min_days_between_orders", "max_days_between_orders"]:
        order_stats[col] = order_stats[col].round(2)

    # Preferred day of week (mode per user)
    preferred_dow = (
        prior_orders.groupby("user_id")["order_dow"]
        .agg(lambda x: x.mode().iloc[0])
        .reset_index()
        .rename(columns={"order_dow": "preferred_order_dow"})
    )

    # Preferred hour (mode per user)
    preferred_hour = (
        prior_orders.groupby("user_id")["order_hour_of_day"]
        .agg(lambda x: x.mode().iloc[0])
        .reset_index()
        .rename(columns={"order_hour_of_day": "preferred_order_hour"})
    )

    logger.info(f"  Order stats: {len(order_stats):,} users")

    # ── Feature 2: Product-level stats from prior table ────────────────────────
    logger.info("Building product-level features ...")

    # Join prior with orders to get user_id
    prior_with_user = prior.merge(
        prior_orders[["order_id", "user_id"]],
        on="order_id", how="inner"
    )

    product_stats = prior_with_user.groupby("user_id").agg(
        total_products       = ("product_id",        "count"),
        unique_products      = ("product_id",        "nunique"),
        reorder_count        = ("reordered",         "sum"),
        reorder_rate         = ("reordered",         "mean"),
        avg_cart_position    = ("add_to_cart_order", "mean"),
    ).reset_index()

    product_stats["reorder_rate"]      = product_stats["reorder_rate"].round(4)
    product_stats["avg_cart_position"] = product_stats["avg_cart_position"].round(2)

    # Avg order size = total_products / total_orders
    # Will be computed after merge

    # ── Feature 3: Department & Aisle diversity ────────────────────────────────
    logger.info("Building diversity features ...")

    prior_with_product = prior_with_user.merge(
        prods, on="product_id", how="left"
    )

    diversity_stats = prior_with_product.groupby("user_id").agg(
        unique_departments = ("department_id", "nunique"),
        unique_aisles      = ("aisle_id",      "nunique"),
    ).reset_index()

    logger.info(f"  Product stats: {len(product_stats):,} users")

    # ── Assemble final feature table ───────────────────────────────────────────
    logger.info("Assembling customer features ...")

    features = (
        order_stats
        .merge(preferred_dow,  on="user_id", how="left")
        .merge(preferred_hour, on="user_id", how="left")
        .merge(product_stats,  on="user_id", how="left")
        .merge(diversity_stats, on="user_id", how="left")
    )

    # Derived: avg_order_size
    features["avg_order_size"] = (
        features["total_products"] / features["total_orders"]
    ).round(2)

    # Derived: product_diversity (unique/total — novelty rate)
    features["product_diversity"] = (
        features["unique_products"] / features["total_products"]
    ).round(4)

    # Reorder count as int
    features["reorder_count"] = features["reorder_count"].astype("int32")

    # Column ordering
    col_order = [
        "user_id",
        "total_orders",
        "avg_order_size",
        "total_products",
        "unique_products",
        "reorder_count",
        "reorder_rate",
        "avg_days_between_orders",
        "std_days_between_orders",
        "min_days_between_orders",
        "max_days_between_orders",
        "preferred_order_dow",
        "preferred_order_hour",
        "unique_departments",
        "unique_aisles",
        "product_diversity",
        "avg_cart_position",
    ]
    features = features[col_order]

    logger.info(f"  Customer features: {len(features):,} users × {len(features.columns)} features")
    return features


def main():
    logger.info("=" * 60)
    logger.info("PHASE 9: Customer Features — START")
    logger.info("=" * 60)

    t_start = time.time()
    features = build_customer_features()

    # Validate
    assert features["user_id"].is_unique, "user_id is not unique in customer features!"
    assert (features["reorder_rate"].between(0, 1)).all(), "reorder_rate out of [0,1]!"
    assert (features["total_orders"] >= 1).all(), "total_orders < 1 found!"
    logger.info("  ✅ All assertions passed")

    # Save
    out_path = PROCESSED_DIR / "customer_features.parquet"
    features.to_parquet(out_path, index=False)
    size_mb = out_path.stat().st_size / (1024 * 1024)
    elapsed = time.time() - t_start

    logger.info(f"  ✅ Saved: {out_path} ({size_mb:.1f} MB)")
    logger.info(f"\n{'='*60}")
    logger.info(f"PHASE 9: Customer Features — COMPLETE ({elapsed:.1f}s)")
    logger.info(f"{'='*60}")

    print("\n" + "=" * 50)
    print("  CUSTOMER FEATURES COMPLETE")
    print("=" * 50)
    print(f"  Users:    {len(features):,}")
    print(f"  Features: {len(features.columns)}")
    print(f"  Output:   data/Processed/customer_features.parquet ({size_mb:.1f} MB)")
    print(f"  Time:     {elapsed:.1f}s")
    print("=" * 50)
    print("\nFeature summary:")
    print(features.describe().round(2).to_string())


if __name__ == "__main__":
    main()
