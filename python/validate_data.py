"""
validate_data.py
================
Enterprise Retail Intelligence & Decision Engine
Phase 5: Data Validation

Validates the cleaned Parquet files in data/Processed/.
Runs hard assertions on critical rules — script exits non-zero on failure.
Produces a clear PASS/FAIL summary to stdout and logs/.

Usage:
    python python/validate_data.py

Exit codes:
    0 — All validations PASS
    1 — One or more critical validations FAIL
"""

import sys
import logging
import time
from pathlib import Path
from datetime import datetime

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
        logging.FileHandler(LOG_DIR / "validate_data.log", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ─── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT  = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "Processed"
REPORTS_DIR   = PROJECT_ROOT / "reports"

# ─── Validation Result Tracking ────────────────────────────────────────────────
RESULTS: list[dict] = []
CRITICAL_FAILURES: list[str] = []


def check(name: str, condition: bool, critical: bool = True,
          detail: str = "") -> bool:
    """
    Record a validation check result.

    Args:
        name:      Human-readable check name.
        condition: True = PASS, False = FAIL.
        critical:  If True and condition is False, will cause exit(1).
        detail:    Additional detail to include in the report.

    Returns:
        condition value (True/False)
    """
    status = "PASS" if condition else "FAIL"
    level  = "CRITICAL" if (not condition and critical) else ("WARNING" if not condition else "OK")

    RESULTS.append({
        "check":    name,
        "status":   status,
        "critical": critical,
        "detail":   detail,
    })

    if condition:
        logger.info(f"  ✅ PASS  | {name}{' | ' + detail if detail else ''}")
    else:
        if critical:
            logger.error(f"  ❌ FAIL  | {name}{' | ' + detail if detail else ''}")
            CRITICAL_FAILURES.append(name)
        else:
            logger.warning(f"  ⚠️  WARN  | {name}{' | ' + detail if detail else ''}")

    return condition


def load(filename: str) -> pd.DataFrame:
    """Load a cleaned Parquet file from Processed/."""
    path = PROCESSED_DIR / filename
    if not path.exists():
        logger.error(f"FILE NOT FOUND: {path}")
        sys.exit(1)
    return pd.read_parquet(path)


def validate_aisles(df: pd.DataFrame) -> None:
    logger.info("\n── Validating: aisles ─────────────────────────────────────")
    check("aisles: row count > 0",             len(df) > 0,                         detail=f"{len(df):,} rows")
    check("aisles: aisle_id uniqueness",        df["aisle_id"].is_unique,            detail="PK")
    check("aisles: no null aisle_id",           df["aisle_id"].notna().all())
    check("aisles: no null aisle",              df["aisle"].notna().all())
    check("aisles: aisle_id >= 1",              (df["aisle_id"] >= 1).all())
    check("aisles: expected ~134 rows",         len(df) == 134,                      detail=f"actual={len(df)}")


def validate_departments(df: pd.DataFrame) -> None:
    logger.info("\n── Validating: departments ────────────────────────────────")
    check("departments: row count > 0",         len(df) > 0,                         detail=f"{len(df):,} rows")
    check("departments: department_id unique",   df["department_id"].is_unique,       detail="PK")
    check("departments: no null department_id",  df["department_id"].notna().all())
    check("departments: no null department",     df["department"].notna().all())
    check("departments: department_id >= 1",     (df["department_id"] >= 1).all())
    check("departments: expected ~21 rows",      len(df) == 21,                       detail=f"actual={len(df)}")


def validate_products(df: pd.DataFrame) -> None:
    logger.info("\n── Validating: products ───────────────────────────────────")
    check("products: row count > 0",            len(df) > 0,                         detail=f"{len(df):,} rows")
    check("products: product_id uniqueness",    df["product_id"].is_unique,          detail="PK")
    check("products: no null product_id",       df["product_id"].notna().all())
    check("products: no null product_name",     df["product_name"].notna().all())
    check("products: no null aisle_id",         df["aisle_id"].notna().all())
    check("products: no null department_id",    df["department_id"].notna().all())
    check("products: product_id >= 1",          (df["product_id"] >= 1).all())
    check("products: aisle_id >= 1",            (df["aisle_id"] >= 1).all())
    check("products: department_id >= 1",       (df["department_id"] >= 1).all())

    # No empty product names after strip
    empty_names = (df["product_name"].str.strip() == "").sum()
    check("products: no empty product_name strings", empty_names == 0,
          detail=f"empty={empty_names}")

    check("products: expected ~49688 rows",     len(df) == 49688,                    detail=f"actual={len(df)}")


def validate_orders(df: pd.DataFrame) -> None:
    logger.info("\n── Validating: orders ─────────────────────────────────────")
    check("orders: row count > 0",              len(df) > 0,                         detail=f"{len(df):,} rows")
    check("orders: order_id uniqueness",        df["order_id"].is_unique,            detail="PK")
    check("orders: no null order_id",           df["order_id"].notna().all())
    check("orders: no null user_id",            df["user_id"].notna().all())
    check("orders: no null eval_set",           df["eval_set"].notna().all())
    check("orders: no null order_number",       df["order_number"].notna().all())
    check("orders: order_number >= 1",          (df["order_number"] >= 1).all())

    # order_dow in [0, 6]
    check("orders: order_dow in [0,6]",
          df["order_dow"].between(0, 6).all(),
          detail=f"min={df['order_dow'].min()}, max={df['order_dow'].max()}")

    # order_hour_of_day in [0, 23]
    check("orders: order_hour_of_day in [0,23]",
          df["order_hour_of_day"].between(0, 23).all(),
          detail=f"min={df['order_hour_of_day'].min()}, max={df['order_hour_of_day'].max()}")

    # days_since_prior_order: NULL only for first orders (order_number == 1)
    first_orders  = df[df["order_number"] == 1]
    later_orders  = df[df["order_number"] > 1]
    null_in_later = later_orders["days_since_prior_order"].isna().sum()
    null_in_first = first_orders["days_since_prior_order"].isna().sum()

    check("orders: days_since_prior NULL only in order_number==1",
          null_in_later == 0,
          detail=f"nulls_in_later_orders={null_in_later}")
    check("orders: first orders have NULL days_since_prior (expected)",
          null_in_first > 0, critical=False,
          detail=f"first_order_nulls={null_in_first:,}")

    # days_since_prior_order in [0, 30] for non-null (Instacart caps at 30)
    non_null_days = df["days_since_prior_order"].dropna()
    check("orders: days_since_prior_order >= 0",
          (non_null_days >= 0).all(),
          detail=f"min={non_null_days.min()}")
    check("orders: days_since_prior_order <= 30",
          (non_null_days <= 30).all(),
          critical=False,
          detail=f"max={non_null_days.max()}")

    # eval_set only contains expected values
    valid_eval_sets = {"prior", "train", "test"}
    actual_eval_sets = set(df["eval_set"].unique())
    check("orders: eval_set values are {prior, train, test}",
          actual_eval_sets.issubset(valid_eval_sets),
          detail=f"found={actual_eval_sets}")

    # is_first_order derived column exists and is valid
    check("orders: is_first_order column exists",        "is_first_order" in df.columns)
    check("orders: is_first_order in {0,1}",
          df["is_first_order"].isin([0, 1]).all())
    check("orders: is_first_order==1 count == first_orders count",
          df["is_first_order"].sum() == len(first_orders),
          detail=f"is_first_order sum={df['is_first_order'].sum():,}, first_orders={len(first_orders):,}")

    # user_id should be positive integers
    check("orders: user_id >= 1",                (df["user_id"] >= 1).all())

    # Each user's order_number should start at 1
    min_order_num_per_user = df.groupby("user_id")["order_number"].min()
    all_start_at_1 = (min_order_num_per_user == 1).all()
    check("orders: each user starts at order_number=1",
          all_start_at_1,
          detail=f"users not starting at 1: {(min_order_num_per_user != 1).sum()}")


def validate_order_products(df: pd.DataFrame, name: str,
                             valid_order_ids: set, valid_product_ids: set) -> None:
    logger.info(f"\n── Validating: {name} ─────────────────────────────")
    check(f"{name}: row count > 0",             len(df) > 0,                         detail=f"{len(df):,} rows")
    check(f"{name}: no null order_id",          df["order_id"].notna().all())
    check(f"{name}: no null product_id",        df["product_id"].notna().all())
    check(f"{name}: no null add_to_cart_order", df["add_to_cart_order"].notna().all())
    check(f"{name}: no null reordered",         df["reordered"].notna().all())

    # Composite PK uniqueness
    composite_dupes = df.duplicated(subset=["order_id", "product_id"]).sum()
    check(f"{name}: composite PK (order_id+product_id) unique",
          composite_dupes == 0,
          detail=f"dupes={composite_dupes:,}")

    # reordered in {0, 1}
    check(f"{name}: reordered in {{0,1}}",
          df["reordered"].isin([0, 1]).all(),
          detail=f"unique_vals={sorted(df['reordered'].unique().tolist())}")

    # add_to_cart_order >= 1
    check(f"{name}: add_to_cart_order >= 1",
          (df["add_to_cart_order"] >= 1).all(),
          detail=f"min={df['add_to_cart_order'].min()}")

    # FK: order_id must exist in orders
    orphan_orders = set(df["order_id"].unique()) - valid_order_ids
    check(f"{name}: FK order_id → orders (no orphans)",
          len(orphan_orders) == 0,
          detail=f"orphan_order_ids={len(orphan_orders):,}")

    # FK: product_id must exist in products
    orphan_products = set(df["product_id"].unique()) - valid_product_ids
    check(f"{name}: FK product_id → products (no orphans)",
          len(orphan_products) == 0,
          detail=f"orphan_product_ids={len(orphan_products):,}")

    # Reorder rate sanity check: must be between 0 and 1 (exclusive for meaningful data)
    reorder_rate = df["reordered"].mean()
    check(f"{name}: reorder_rate between 0 and 1",
          0 <= reorder_rate <= 1,
          detail=f"overall_reorder_rate={reorder_rate:.4f}")


def write_validation_report(elapsed: float) -> Path:
    """Write a PASS/FAIL validation summary to reports/."""
    out_path = REPORTS_DIR / "validation_report.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    passes   = sum(1 for r in RESULTS if r["status"] == "PASS")
    fails    = sum(1 for r in RESULTS if r["status"] == "FAIL")
    warnings = sum(1 for r in RESULTS if r["status"] == "FAIL" and not r["critical"])
    critical = sum(1 for r in RESULTS if r["status"] == "FAIL" and r["critical"])

    overall  = "✅ ALL CRITICAL CHECKS PASS" if critical == 0 else f"❌ {critical} CRITICAL FAILURES"

    lines = [
        "# Enterprise Retail Intelligence & Decision Engine",
        "## Data Validation Report",
        "",
        f"**Generated:** {now}  ",
        "**Phase:** 5 — Data Validation  ",
        f"**Overall Status:** {overall}  ",
        f"**Time Elapsed:** {elapsed:.1f}s  ",
        "",
        "---",
        "",
        f"## Summary",
        "",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Total Checks | {len(RESULTS)} |",
        f"| PASS | {passes} |",
        f"| FAIL (Critical) | {critical} |",
        f"| FAIL (Warning) | {warnings} |",
        "",
        "---",
        "",
        "## Check Results",
        "",
        "| Check | Status | Detail |",
        "|-------|--------|--------|",
    ]

    for r in RESULTS:
        icon = "✅" if r["status"] == "PASS" else ("❌" if r["critical"] else "⚠️")
        lines.append(f"| {r['check']} | {icon} {r['status']} | {r['detail']} |")

    if CRITICAL_FAILURES:
        lines += [
            "",
            "---",
            "",
            "## Critical Failures",
            "",
        ]
        for f in CRITICAL_FAILURES:
            lines.append(f"- ❌ `{f}`")

    lines += [
        "",
        "---",
        "",
        "*Generated by python/validate_data.py — Phase 5*",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main():
    logger.info("=" * 60)
    logger.info("PHASE 5: Data Validation — START")
    logger.info("=" * 60)

    start = time.time()

    # Load reference sets for FK checks
    logger.info("\nLoading reference tables for FK validation ...")
    aisles       = load("aisles_clean.parquet")
    departments  = load("departments_clean.parquet")
    products     = load("products_clean.parquet")
    orders       = load("orders_clean.parquet")
    prior        = load("order_products_prior_clean.parquet")
    train        = load("order_products_train_clean.parquet")

    valid_aisle_ids  = set(aisles["aisle_id"].unique())
    valid_dept_ids   = set(departments["department_id"].unique())
    valid_prod_ids   = set(products["product_id"].unique())
    valid_order_ids  = set(orders["order_id"].unique())

    # ── Run all validations ──────────────────────────────────────────────────────
    validate_aisles(aisles)
    validate_departments(departments)

    # Products with FK validation
    logger.info("\n── Validating: products (with FK checks) ──────────────────")
    validate_products(products)
    orphan_aisles = set(products["aisle_id"].unique()) - valid_aisle_ids
    check("products: FK aisle_id → aisles (no orphans)",
          len(orphan_aisles) == 0, detail=f"orphans={len(orphan_aisles)}")
    orphan_depts = set(products["department_id"].unique()) - valid_dept_ids
    check("products: FK department_id → departments (no orphans)",
          len(orphan_depts) == 0, detail=f"orphans={len(orphan_depts)}")

    validate_orders(orders)
    validate_order_products(prior,  "order_products_prior",  valid_order_ids, valid_prod_ids)
    validate_order_products(train,  "order_products_train",  valid_order_ids, valid_prod_ids)

    # ── Cross-table sanity checks ────────────────────────────────────────────────
    logger.info("\n── Cross-table sanity checks ──────────────────────────────")

    # All prior order_ids should have eval_set = 'prior' in orders
    prior_order_ids_in_orders = orders[orders["eval_set"] == "prior"]["order_id"]
    orphan_prior = set(prior["order_id"].unique()) - set(prior_order_ids_in_orders.unique())
    check("cross: prior orders all have eval_set='prior' in orders",
          len(orphan_prior) == 0,
          detail=f"mismatched={len(orphan_prior)}")

    # All train order_ids should have eval_set = 'train' in orders
    train_order_ids_in_orders = orders[orders["eval_set"] == "train"]["order_id"]
    orphan_train = set(train["order_id"].unique()) - set(train_order_ids_in_orders.unique())
    check("cross: train orders all have eval_set='train' in orders",
          len(orphan_train) == 0,
          detail=f"mismatched={len(orphan_train)}")

    # Number of unique users
    n_users = orders["user_id"].nunique()
    check("cross: unique user count reasonable (> 100000)",
          n_users > 100000, critical=False,
          detail=f"unique_users={n_users:,}")

    # Average basket size sanity
    avg_basket_prior = len(prior) / prior["order_id"].nunique()
    check("cross: average basket size (prior) between 1 and 100",
          1 <= avg_basket_prior <= 100,
          detail=f"avg_basket={avg_basket_prior:.2f}")

    elapsed = time.time() - start

    # ── Write report ─────────────────────────────────────────────────────────────
    logger.info("\nWriting validation report ...")
    report_path = write_validation_report(elapsed)
    logger.info(f"  ✅ Written: {report_path}")

    # ── Final summary ────────────────────────────────────────────────────────────
    passes   = sum(1 for r in RESULTS if r["status"] == "PASS")
    fails    = sum(1 for r in RESULTS if r["status"] == "FAIL")
    critical = sum(1 for r in RESULTS if r["status"] == "FAIL" and r["critical"])

    logger.info("\n" + "=" * 60)
    logger.info(f"PHASE 5: Data Validation — {'COMPLETE ✅' if critical == 0 else 'FAILED ❌'}")
    logger.info("=" * 60)

    print("\n" + "=" * 50)
    print("  VALIDATION SUMMARY")
    print("=" * 50)
    print(f"  Total checks    : {len(RESULTS)}")
    print(f"  PASS            : {passes}")
    print(f"  FAIL (critical) : {critical}")
    print(f"  FAIL (warning)  : {fails - critical}")
    print(f"  Time elapsed    : {elapsed:.1f}s")
    print(f"  Report          : reports/validation_report.md")
    print("=" * 50)

    if critical > 0:
        print("\n❌ CRITICAL FAILURES DETECTED:")
        for f in CRITICAL_FAILURES:
            print(f"   - {f}")
        sys.exit(1)
    else:
        print("\n✅ All critical validations passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
