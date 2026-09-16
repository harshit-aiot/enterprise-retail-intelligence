"""
customer_segmentation.py
========================
Enterprise Retail Intelligence & Decision Engine
Phase 10: Customer Segmentation

Performs K-Means clustering on customer behavioral features.
Segments are named AFTER inspecting cluster characteristics — not before.

Steps:
    1. Load customer_features.parquet
    2. Select clustering features
    3. Scale features
    4. Determine optimal K (elbow + silhouette)
    5. Fit K-Means
    6. Profile clusters
    7. Assign descriptive names based on evidence
    8. Save results

Output:
    data/Processed/customer_segments.parquet
    reports/customer_segments.md
"""

import sys
import logging
import time
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "customer_segmentation.log", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

PROJECT_ROOT  = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "Processed"
REPORTS_DIR   = PROJECT_ROOT / "reports"

# Clustering features — all behavioral, no demographics
CLUSTER_FEATURES = [
    "total_orders",
    "avg_order_size",
    "reorder_rate",
    "avg_days_between_orders",
    "unique_departments",
    "product_diversity",
    "avg_cart_position",
]


def find_optimal_k(X_scaled: np.ndarray, k_range: range) -> tuple[int, dict]:
    """
    Determine optimal K using elbow (inertia) and silhouette score.
    Returns best_k and metrics dict.
    """
    metrics = {"k": [], "inertia": [], "silhouette": []}

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
        labels = km.fit_predict(X_scaled)
        sil = silhouette_score(X_scaled, labels, sample_size=min(10000, len(X_scaled)), random_state=42)
        metrics["k"].append(k)
        metrics["inertia"].append(km.inertia_)
        metrics["silhouette"].append(sil)
        logger.info(f"  k={k}: inertia={km.inertia_:.0f}, silhouette={sil:.4f}")

    # Best K by silhouette
    best_idx = int(np.argmax(metrics["silhouette"]))
    best_k   = metrics["k"][best_idx]
    logger.info(f"  → Best K by silhouette: {best_k} (score={metrics['silhouette'][best_idx]:.4f})")
    return best_k, metrics


def profile_clusters(df: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
    """Compute per-cluster statistics for profiling."""
    profile = df.groupby("cluster")[feature_cols + ["user_id"]].agg(
        cluster_size        = ("user_id", "count"),
        avg_total_orders    = ("total_orders", "mean"),
        avg_order_size      = ("avg_order_size", "mean"),
        avg_reorder_rate    = ("reorder_rate", "mean"),
        avg_days_between    = ("avg_days_between_orders", "mean"),
        avg_dept_diversity  = ("unique_departments", "mean"),
        avg_product_diversity = ("product_diversity", "mean"),
        avg_cart_position   = ("avg_cart_position", "mean"),
    ).reset_index()

    for col in profile.select_dtypes(include="float").columns:
        profile[col] = profile[col].round(3)
    return profile


def assign_segment_names(profile: pd.DataFrame) -> dict:
    """
    Assign descriptive segment names based on actual cluster statistics.
    Names are derived from data — not pre-assigned.
    Returns dict: cluster → segment_name
    """
    names = {}
    for _, row in profile.iterrows():
        k = row["cluster"]
        orders    = row["avg_total_orders"]
        reorder   = row["avg_reorder_rate"]
        days      = row["avg_days_between"]
        diversity = row["avg_product_diversity"]
        basket    = row["avg_order_size"]

        if orders >= 15 and reorder >= 0.60 and days <= 10:
            name = "Champion Loyalists"
        elif orders >= 10 and reorder >= 0.55:
            name = "Loyal Regulars"
        elif orders >= 10 and reorder < 0.50 and diversity >= 0.5:
            name = "Explorers"
        elif orders < 7 and days > 18:
            name = "Infrequent Shoppers"
        elif basket >= 12 and orders >= 8:
            name = "Bulk Buyers"
        else:
            name = "Occasional Buyers"

        names[k] = name
        logger.info(f"  Cluster {k}: '{name}' (orders={orders:.1f}, reorder={reorder:.2f}, days={days:.1f})")

    return names


def write_segments_report(profile: pd.DataFrame, segment_names: dict,
                          best_k: int, sil_score: float) -> None:
    now = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Enterprise Retail Intelligence & Decision Engine",
        "## Customer Segmentation Report",
        "",
        f"**Generated:** {now}  ",
        "**Phase:** 10 — Customer Segmentation  ",
        f"**Method:** K-Means Clustering (K={best_k})  ",
        f"**Silhouette Score:** {sil_score:.4f}  ",
        "",
        "---",
        "",
        "## Methodology",
        "",
        "- **Algorithm:** K-Means (scikit-learn, random_state=42, n_init=10)",
        "- **Features used:** total_orders, avg_order_size, reorder_rate, avg_days_between_orders, unique_departments, product_diversity, avg_cart_position",
        "- **Feature scaling:** StandardScaler (zero mean, unit variance)",
        "- **K selection:** Evaluated K=2 to 7 using silhouette score; best K chosen by highest silhouette",
        "- **Segment names:** Assigned AFTER inspecting actual cluster statistics — not predetermined",
        "- **No demographic data used** — purely behavioral segmentation",
        "",
        "---",
        "",
        "## Segment Profiles",
        "",
        "| Segment | Size | Avg Orders | Reorder Rate | Avg Days Between | Avg Basket | Dept Diversity | Product Diversity |",
        "|---------|------|------------|--------------|------------------|------------|----------------|-------------------|",
    ]

    total_customers = profile["cluster_size"].sum()
    for _, row in profile.iterrows():
        k    = row["cluster"]
        name = segment_names.get(k, f"Cluster {k}")
        pct  = round(row["cluster_size"] * 100 / total_customers, 1)
        lines.append(
            f"| **{name}** | {row['cluster_size']:,} ({pct}%) | "
            f"{row['avg_total_orders']:.1f} | {row['avg_reorder_rate']*100:.1f}% | "
            f"{row['avg_days_between']:.1f} days | {row['avg_order_size']:.1f} items | "
            f"{row['avg_dept_diversity']:.1f} depts | {row['avg_product_diversity']:.2f} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Segment Business Interpretations",
        "",
    ]

    interpretations = {
        "Champion Loyalists":  "Highly frequent, high reorder rate. Core customer base — prioritize retention. Most responsive to loyalty programs.",
        "Loyal Regulars":      "Regular purchasers with strong reorder habits. Established patterns — good cross-sell opportunities.",
        "Explorers":           "Order frequently but try new products. Responsive to new product introductions and discovery features.",
        "Infrequent Shoppers": "Low frequency, long gaps between orders. May be lapsed or seasonal. Re-engagement campaigns may be relevant.",
        "Bulk Buyers":         "Large basket sizes per order. Prefer stocking up in fewer visits. Bundling opportunities.",
        "Occasional Buyers":   "Low frequency, moderate behavior. May be transitioning customers or occasional supplement shoppers.",
    }

    for k, name in segment_names.items():
        desc = interpretations.get(name, "Behavioral pattern differs from standard segments.")
        lines += [f"### {name}", "", f"{desc}", "", f"> **Limitation:** Interpretations are based on observed behavioral patterns only. No revenue, demographics, or intent data is available.", ""]

    lines += [
        "---",
        "",
        "## Limitations",
        "",
        "- No revenue or profit data available — segments reflect behavior, not value",
        "- No demographic data — segments are purely behavioral",
        "- Dataset has no timestamps — temporal dynamics cannot be modeled",
        "- K-Means assumes spherical clusters — some overlap is expected",
        "",
        "---",
        "*Generated by python/customer_segmentation.py — Phase 10*",
    ]

    (REPORTS_DIR / "customer_segments.md").write_text("\n".join(lines), encoding="utf-8")
    logger.info("  ✅ customer_segments.md written")


def main():
    logger.info("=" * 60)
    logger.info("PHASE 10: Customer Segmentation — START")
    logger.info("=" * 60)

    t_start = time.time()

    # Load features
    logger.info("\nLoading customer features ...")
    df = pd.read_parquet(PROCESSED_DIR / "customer_features.parquet")
    logger.info(f"  {len(df):,} customers, {len(df.columns)} features")

    # Handle NaN in avg_days (users with 1 order have no days_since_prior)
    for col in CLUSTER_FEATURES:
        if df[col].isna().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            logger.info(f"  Filled {col} NaN with median ({median_val:.2f})")

    X = df[CLUSTER_FEATURES].values
    logger.info(f"  Feature matrix: {X.shape}")

    # Scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Find optimal K
    logger.info("\nFinding optimal K (evaluating K=2 to 7) ...")
    best_k, metrics = find_optimal_k(X_scaled, range(2, 8))

    # Fit final model
    logger.info(f"\nFitting K-Means with K={best_k} ...")
    km = KMeans(n_clusters=best_k, random_state=42, n_init=20, max_iter=500)
    df["cluster"] = km.fit_predict(X_scaled)
    final_sil = silhouette_score(X_scaled, df["cluster"],
                                  sample_size=min(10000, len(df)), random_state=42)
    logger.info(f"  Final silhouette score: {final_sil:.4f}")

    # Profile clusters
    logger.info("\nProfiling clusters ...")
    profile = profile_clusters(df, CLUSTER_FEATURES)
    logger.info(f"\n{profile.to_string()}")

    # Assign names
    logger.info("\nAssigning segment names ...")
    segment_names = assign_segment_names(profile)
    df["segment"] = df["cluster"].map(segment_names)

    # Save
    out_path = PROCESSED_DIR / "customer_segments.parquet"
    df[["user_id", "cluster", "segment"] + CLUSTER_FEATURES].to_parquet(out_path, index=False)
    logger.info(f"  ✅ Saved: {out_path}")

    # Write report
    write_segments_report(profile, segment_names, best_k, final_sil)

    elapsed = time.time() - t_start
    logger.info(f"\n{'='*60}")
    logger.info(f"PHASE 10: Customer Segmentation — COMPLETE ({elapsed:.1f}s)")
    logger.info(f"{'='*60}")

    print("\n" + "=" * 50)
    print("  CUSTOMER SEGMENTATION COMPLETE")
    print("=" * 50)
    print(f"  Customers segmented : {len(df):,}")
    print(f"  Segments (K)        : {best_k}")
    print(f"  Silhouette Score    : {final_sil:.4f}")
    print(f"  Segment distribution:")
    for k, name in segment_names.items():
        cnt = (df["cluster"] == k).sum()
        print(f"    [{k}] {name:<30} {cnt:,} ({cnt*100/len(df):.1f}%)")
    print("=" * 50)


if __name__ == "__main__":
    main()
