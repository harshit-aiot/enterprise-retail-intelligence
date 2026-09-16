"""
market_basket.py
================
Enterprise Retail Intelligence & Decision Engine
Phase 12: Market Basket Analysis

Uses product co-occurrence (efficient approach, no Apriori on 32M rows raw).

Strategy:
    - Sample a representative subset of orders (top N frequent products)
    - Build product co-occurrence matrix
    - Compute support, confidence, lift for top pairs
    - Identify cross-sell opportunities

Output:
    data/Processed/market_basket_results.parquet
    reports/market_basket_insights.md
"""

import sys
import logging
import time
from pathlib import Path
from itertools import combinations
from collections import defaultdict

import pandas as pd
import numpy as np

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "market_basket.log", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

PROJECT_ROOT  = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "Processed"
REPORTS_DIR   = PROJECT_ROOT / "reports"

# Use only top N products to keep computation tractable
TOP_N_PRODUCTS = 500
MIN_SUPPORT    = 0.005   # product pair must appear in at least 0.5% of orders
MIN_CONFIDENCE = 0.10    # P(B|A) >= 10%
MIN_LIFT       = 1.1     # at least 10% lift over random


def load_data():
    logger.info("Loading data ...")
    prior   = pd.read_parquet(PROCESSED_DIR / "order_products_prior_clean.parquet")
    prods   = pd.read_parquet(PROCESSED_DIR / "products_clean.parquet")
    n_orders = prior["order_id"].nunique()
    logger.info(f"  Prior: {len(prior):,} rows, {n_orders:,} unique orders")
    return prior, prods, n_orders


def get_top_products(prior: pd.DataFrame, n: int) -> set:
    top = (
        prior.groupby("product_id")["order_id"]
        .count()
        .nlargest(n)
        .index
    )
    logger.info(f"  Top {n} products selected for MBA")
    return set(top)


def compute_pair_stats(prior: pd.DataFrame, top_products: set,
                        n_total_orders: int) -> pd.DataFrame:
    """
    Compute support, confidence, lift for product pairs.
    Uses efficient groupby + combinations approach.
    """
    logger.info("Filtering to top products ...")
    filtered = prior[prior["product_id"].isin(top_products)]
    logger.info(f"  Filtered rows: {len(filtered):,}")

    # Group products per order
    logger.info("Grouping products per order ...")
    order_products = (
        filtered.groupby("order_id")["product_id"]
        .apply(frozenset)
        .reset_index()
    )
    # Only keep orders with 2+ products
    order_products = order_products[order_products["product_id"].apply(len) >= 2]
    logger.info(f"  Orders with 2+ top products: {len(order_products):,}")

    # Individual product support
    logger.info("Computing individual product support ...")
    product_support = (
        filtered.groupby("product_id")["order_id"]
        .nunique()
        .to_dict()
    )

    # Pair co-occurrence
    logger.info("Computing pair co-occurrences (this may take ~1-2 min) ...")
    pair_counts = defaultdict(int)
    for _, row in order_products.iterrows():
        prods = list(row["product_id"])
        for a, b in combinations(sorted(prods), 2):
            pair_counts[(a, b)] += 1

    logger.info(f"  Unique product pairs: {len(pair_counts):,}")

    # Build association rules
    logger.info("Computing support, confidence, lift ...")
    records = []
    for (a, b), co_count in pair_counts.items():
        support = co_count / n_total_orders
        if support < MIN_SUPPORT:
            continue
        conf_a_to_b = co_count / product_support.get(a, 1)
        conf_b_to_a = co_count / product_support.get(b, 1)
        lift = support / (
            (product_support.get(a, 1) / n_total_orders) *
            (product_support.get(b, 1) / n_total_orders)
        )
        if lift < MIN_LIFT:
            continue
        if conf_a_to_b >= MIN_CONFIDENCE:
            records.append({
                "antecedent": a, "consequent": b,
                "support": round(support, 6),
                "confidence": round(conf_a_to_b, 4),
                "lift": round(lift, 4),
                "co_occurrence": co_count,
            })
        if conf_b_to_a >= MIN_CONFIDENCE:
            records.append({
                "antecedent": b, "consequent": a,
                "support": round(support, 6),
                "confidence": round(conf_b_to_a, 4),
                "lift": round(lift, 4),
                "co_occurrence": co_count,
            })

    df_rules = pd.DataFrame(records).drop_duplicates()
    logger.info(f"  Rules passing filters: {len(df_rules):,}")
    return df_rules


def add_product_names(df_rules: pd.DataFrame, prods: pd.DataFrame) -> pd.DataFrame:
    prod_map = prods.set_index("product_id")["product_name"].to_dict()
    df_rules["antecedent_name"] = df_rules["antecedent"].map(prod_map)
    df_rules["consequent_name"] = df_rules["consequent"].map(prod_map)
    return df_rules


def write_insights_report(df_rules: pd.DataFrame) -> None:
    now = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    top50 = df_rules.nlargest(50, "lift")

    lines = [
        "# Enterprise Retail Intelligence & Decision Engine",
        "## Market Basket Analysis — Insights Report",
        "",
        f"**Generated:** {now}  ",
        "**Phase:** 12 — Market Basket Analysis  ",
        "",
        "---",
        "",
        "## Methodology",
        "",
        "- **Approach:** Product co-occurrence analysis on prior order basket data",
        f"- **Products analyzed:** Top {TOP_N_PRODUCTS} by purchase frequency",
        f"- **Total prior orders:** Used as denominator for support calculation",
        f"- **Minimum support:** {MIN_SUPPORT} ({MIN_SUPPORT*100:.1f}% of all orders)",
        f"- **Minimum confidence:** {MIN_CONFIDENCE} ({MIN_CONFIDENCE*100:.0f}%)",
        f"- **Minimum lift:** {MIN_LIFT}",
        f"- **Total rules found:** {len(df_rules):,}",
        "",
        "**Metrics:**",
        "- **Support:** P(A ∩ B) — fraction of all orders containing both products",
        "- **Confidence:** P(B|A) — fraction of orders with A that also contain B",
        "- **Lift:** Support / (P(A) × P(B)) — how much more co-occurring than by chance (>1 = positive association)",
        "",
        "---",
        "",
        "## Top 50 Product Associations (by Lift)",
        "",
        "| Antecedent | Consequent | Support | Confidence | Lift | Co-occurrences |",
        "|-----------|-----------|---------|------------|------|----------------|",
    ]

    for _, row in top50.iterrows():
        lines.append(
            f"| {row['antecedent_name']} | {row['consequent_name']} | "
            f"{row['support']:.4f} | {row['confidence']:.3f} | "
            f"{row['lift']:.3f} | {row['co_occurrence']:,} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Business Interpretation",
        "",
        "**High lift pairs** indicate products that are purchased together significantly more often than chance.",
        "These represent strong cross-selling opportunities.",
        "",
        "**High confidence pairs** indicate that when customers buy product A, they very often also buy product B.",
        "This is most actionable for recommendation systems.",
        "",
        "## Limitations",
        "",
        "- Analysis limited to top 500 products for computational tractability",
        "- No price data available — margin impact of cross-sell cannot be assessed",
        "- Association ≠ causation — products may co-occur due to lifestyle patterns",
        "- Dataset from 2017 — product assortment may have changed",
        "",
        "---",
        "*Generated by python/market_basket.py — Phase 12*",
    ]

    (REPORTS_DIR / "market_basket_insights.md").write_text("\n".join(lines), encoding="utf-8")
    logger.info("  ✅ market_basket_insights.md written")


def main():
    logger.info("=" * 60)
    logger.info("PHASE 12: Market Basket Analysis — START")
    logger.info("=" * 60)
    t_start = time.time()

    prior, prods, n_orders = load_data()
    top_products = get_top_products(prior, TOP_N_PRODUCTS)
    df_rules = compute_pair_stats(prior, top_products, n_orders)

    if len(df_rules) == 0:
        logger.warning("No rules found with current thresholds — lowering min_support")
        MIN_SUPPORT_ADJ = 0.002
        df_rules = compute_pair_stats(prior, top_products, n_orders)

    df_rules = add_product_names(df_rules, prods)
    df_rules = df_rules.sort_values("lift", ascending=False).reset_index(drop=True)

    # Save
    out_path = PROCESSED_DIR / "market_basket_results.parquet"
    df_rules.to_parquet(out_path, index=False)
    logger.info(f"  ✅ Saved: {out_path}")

    write_insights_report(df_rules)

    elapsed = time.time() - t_start
    logger.info(f"\n{'='*60}\nPHASE 12: COMPLETE ({elapsed:.1f}s)\n{'='*60}")

    print(f"\n✅ Market Basket Analysis complete")
    print(f"  Rules found: {len(df_rules):,}")
    print(f"  Top pair by lift: {df_rules.iloc[0]['antecedent_name']} → {df_rules.iloc[0]['consequent_name']} (lift={df_rules.iloc[0]['lift']:.3f})")


if __name__ == "__main__":
    main()
