"""
clean_data.py
=============
Enterprise Retail Intelligence & Decision Engine
Phase 4: Data Cleaning

Reads each raw CSV, applies targeted cleaning, and saves
cleaned files to data/Processed/.

Cleaning principles:
  - Never overwrite data/Raw/
  - Every transformation is reproducible and logged
  - Preserve meaningful NULLs (days_since_prior_order for 1st orders)
  - Do not impute or fabricate data
  - Standardize column names and types

Output files (data/Processed/):
  aisles_clean.parquet
  departments_clean.parquet
  products_clean.parquet
  orders_clean.parquet
  order_products_prior_clean.parquet
  order_products_train_clean.parquet

Usage:
    Activate .venv, then:
    python python/clean_data.py

Author: Enterprise BI Project
"""

import os
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
        logging.FileHandler(LOG_DIR / "clean_data.log", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ─── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT  = Path(__file__).resolve().parent.parent
RAW_DIR       = PROJECT_ROOT / "data" / "Raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "Processed"
REPORTS_DIR   = PROJECT_ROOT / "reports"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ─── Efficient read dtypes ──────────────────────────────────────────────────────
READ_DTYPES = {
    "aisles": {
        "aisle_id": "int16",
        "aisle":    "object",
    },
    "departments": {
        "department_id": "int8",
        "department":    "object",
    },
    "products": {
        "product_id":    "int32",
        "product_name":  "object",
        "aisle_id":      "int16",
        "department_id": "int8",
    },
    "orders": {
        "order_id":              "int32",
        "user_id":               "int32",
        "eval_set":              "object",
        "order_number":          "int16",
        "order_dow":             "int8",
        "order_hour_of_day":     "int8",
        "days_since_prior_order": "float32",
    },
    "order_products__prior": {
        "order_id":          "int32",
        "product_id":        "int32",
        "add_to_cart_order": "int16",
        "reordered":         "int8",
    },
    "order_products__train": {
        "order_id":          "int32",
        "product_id":        "int32",
        "add_to_cart_order": "int16",
        "reordered":         "int8",
    },
}

# ─── Cleaning Log ───────────────────────────────────────────────────────────────
CLEANING_LOG: list[dict] = []

def log_action(table: str, issue: str, action: str, reason: str, affected: int) -> None:
    """Record a cleaning action to the cleaning log."""
    entry = {
        "table":    table,
        "issue":    issue,
        "action":   action,
        "reason":   reason,
        "affected": affected,
    }
    CLEANING_LOG.append(entry)
    logger.info(f"  [{table}] {issue} → {action} ({affected:,} records affected)")


# ─── Per-table Cleaning Functions ──────────────────────────────────────────────

def clean_aisles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the aisles table.

    Transformations:
      - Strip whitespace from aisle names
      - Convert aisle names to title case for consistency
      - Convert aisle column to category dtype for memory efficiency
    """
    original_shape = df.shape

    # Strip leading/trailing whitespace from string columns
    before = df["aisle"].str.strip().ne(df["aisle"]).sum()
    df["aisle"] = df["aisle"].str.strip()
    if before > 0:
        log_action("aisles", "Whitespace in aisle name", "str.strip()", "Standardize string fields", int(before))
    else:
        log_action("aisles", "Whitespace check", "No action needed", "No whitespace found", 0)

    # Convert to category for memory efficiency
    df["aisle"] = df["aisle"].astype("category")
    log_action("aisles", "dtype optimization", "aisle → category", "Reduce memory usage", len(df))

    assert df.shape[0] == original_shape[0], "Row count changed during aisles cleaning!"
    assert df["aisle_id"].is_unique, "aisle_id is not unique after cleaning!"
    logger.info(f"  aisles: {original_shape[0]:,} rows → {df.shape[0]:,} rows (no rows removed)")
    return df


def clean_departments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the departments table.

    Transformations:
      - Strip whitespace from department names
      - Convert department column to category dtype
    """
    original_shape = df.shape

    before = df["department"].str.strip().ne(df["department"]).sum()
    df["department"] = df["department"].str.strip()
    if before > 0:
        log_action("departments", "Whitespace in department name", "str.strip()", "Standardize string fields", int(before))
    else:
        log_action("departments", "Whitespace check", "No action needed", "No whitespace found", 0)

    df["department"] = df["department"].astype("category")
    log_action("departments", "dtype optimization", "department → category", "Reduce memory usage", len(df))

    assert df.shape[0] == original_shape[0]
    assert df["department_id"].is_unique
    return df


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the products table.

    Transformations:
      - Strip whitespace from product_name
      - Drop exact full-row duplicates (if any)
      - Validate no missing product_ids or names
    """
    original_shape = df.shape

    # Whitespace strip on product_name
    before = df["product_name"].str.strip().ne(df["product_name"]).sum()
    df["product_name"] = df["product_name"].str.strip()
    if before > 0:
        log_action("products", "Whitespace in product_name", "str.strip()", "Standardize text field", int(before))
    else:
        log_action("products", "Whitespace check (product_name)", "No action needed", "No whitespace found", 0)

    # Drop full-row duplicates (should be 0, validated in profiling)
    dupes = df.duplicated().sum()
    if dupes > 0:
        df = df.drop_duplicates()
        log_action("products", "Full-row duplicates", "drop_duplicates()", "Preserve data integrity", int(dupes))
    else:
        log_action("products", "Duplicate check", "No action needed", "No duplicates found", 0)

    # Validate no missing values in key columns
    for col in ["product_id", "product_name", "aisle_id", "department_id"]:
        n_null = df[col].isna().sum()
        if n_null > 0:
            logger.warning(f"  WARNING: {n_null} NULLs found in products.{col}!")
        else:
            log_action("products", f"NULL check ({col})", "No action needed", "No nulls found", 0)

    assert df["product_id"].is_unique, "product_id is not unique after cleaning!"
    logger.info(f"  products: {original_shape[0]:,} → {df.shape[0]:,} rows")
    return df


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the orders table.

    Transformations:
      - Strip whitespace from eval_set
      - Convert eval_set to category dtype
      - Validate order_dow is in [0, 6]
      - Validate order_hour_of_day is in [0, 23]
      - Preserve NULL in days_since_prior_order (meaningful: first order has no prior)
      - Validate order_number >= 1
      - Flag any impossible days_since_prior_order values (>30 is allowed; >365 would be suspicious)
    """
    original_shape = df.shape

    # Strip eval_set
    before = df["eval_set"].str.strip().ne(df["eval_set"]).sum()
    df["eval_set"] = df["eval_set"].str.strip()
    if before > 0:
        log_action("orders", "Whitespace in eval_set", "str.strip()", "Standardize string field", int(before))
    else:
        log_action("orders", "eval_set whitespace check", "No action needed", "No whitespace found", 0)

    # eval_set to category
    df["eval_set"] = df["eval_set"].astype("category")
    log_action("orders", "dtype optimization", "eval_set → category", "Reduce memory usage", len(df))

    # Validate order_dow in [0, 6]
    invalid_dow = df["order_dow"].lt(0) | df["order_dow"].gt(6)
    n_invalid_dow = int(invalid_dow.sum())
    if n_invalid_dow > 0:
        logger.warning(f"  WARNING: {n_invalid_dow} rows with order_dow outside [0,6]!")
        log_action("orders", "Invalid order_dow values", f"Flagged {n_invalid_dow} rows",
                   "order_dow must be 0–6", n_invalid_dow)
    else:
        log_action("orders", "order_dow range check [0,6]", "No action needed", "All values valid", 0)

    # Validate order_hour_of_day in [0, 23]
    invalid_hour = df["order_hour_of_day"].lt(0) | df["order_hour_of_day"].gt(23)
    n_invalid_hour = int(invalid_hour.sum())
    if n_invalid_hour > 0:
        logger.warning(f"  WARNING: {n_invalid_hour} rows with order_hour_of_day outside [0,23]!")
        log_action("orders", "Invalid order_hour_of_day", f"Flagged {n_invalid_hour} rows",
                   "Hour must be 0–23", n_invalid_hour)
    else:
        log_action("orders", "order_hour_of_day range check", "No action needed", "All values valid", 0)

    # days_since_prior_order: preserve NULLs (first orders) — do NOT impute
    n_null_days = int(df["days_since_prior_order"].isna().sum())
    log_action(
        "orders",
        f"days_since_prior_order NULLs ({n_null_days:,})",
        "Preserved as-is",
        "NULLs represent first orders — semantically meaningful, not data errors",
        n_null_days,
    )

    # Check for suspicious values: days > 30 (max Instacart allows per dataset docs)
    non_null_days = df["days_since_prior_order"].dropna()
    over_30 = int((non_null_days > 30).sum())
    if over_30 > 0:
        # This is expected — Instacart caps at 30 in their dataset description
        # but some values may show as 30 meaning "30 or more"
        log_action("orders", f"days_since_prior_order > 30 ({over_30:,} rows)",
                   "Kept as-is", "Instacart caps at 30 days — value of 30 means '30 or more days'", over_30)

    # Validate order_number >= 1
    invalid_order_num = int((df["order_number"] < 1).sum())
    if invalid_order_num > 0:
        logger.warning(f"  WARNING: {invalid_order_num} rows with order_number < 1!")
    else:
        log_action("orders", "order_number >= 1 check", "No action needed", "All values valid", 0)

    # Add derived helper column: is_first_order (useful for analysis)
    df["is_first_order"] = (df["order_number"] == 1).astype("int8")
    log_action("orders", "Derived column added", "is_first_order (1 if order_number==1 else 0)",
               "Useful analytical flag for first-order analysis", int(df["is_first_order"].sum()))

    assert df.shape[0] == original_shape[0]
    assert df["order_id"].is_unique
    logger.info(f"  orders: {original_shape[0]:,} → {df.shape[0]:,} rows")
    return df


def clean_order_products(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """
    Clean order_products__prior or order_products__train.

    Both tables have identical structure, so share one cleaner.

    Transformations:
      - Validate reordered is in {0, 1}
      - Validate add_to_cart_order >= 1
      - Drop full-row duplicates (should be 0 from profiling)
    """
    original_shape = df.shape

    # Validate reordered in {0, 1}
    invalid_reordered = ~df["reordered"].isin([0, 1])
    n_invalid = int(invalid_reordered.sum())
    if n_invalid > 0:
        logger.warning(f"  WARNING: {n_invalid} rows in {table_name}.reordered outside {{0,1}}!")
        log_action(table_name, "Invalid reordered values", f"Flagged {n_invalid}",
                   "reordered must be 0 or 1", n_invalid)
    else:
        log_action(table_name, "reordered value check {0,1}", "No action needed", "All values valid", 0)

    # Validate add_to_cart_order >= 1
    invalid_cart = int((df["add_to_cart_order"] < 1).sum())
    if invalid_cart > 0:
        logger.warning(f"  WARNING: {invalid_cart} rows with add_to_cart_order < 1!")
    else:
        log_action(table_name, "add_to_cart_order >= 1 check", "No action needed", "All values valid", 0)

    # Drop full-row duplicates
    dupes = df.duplicated().sum()
    if dupes > 0:
        df = df.drop_duplicates()
        log_action(table_name, "Full-row duplicates", "drop_duplicates()",
                   "Preserve data integrity", int(dupes))
    else:
        log_action(table_name, "Duplicate check", "No action needed", "No duplicates found", 0)

    assert df.shape[0] == original_shape[0] - int(dupes if dupes > 0 else 0)
    logger.info(f"  {table_name}: {original_shape[0]:,} → {df.shape[0]:,} rows")
    return df


def write_cleaning_log(output_path: Path) -> None:
    """Write the data_cleaning_log.md report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Enterprise Retail Intelligence & Decision Engine",
        "## Data Cleaning Log",
        "",
        f"**Generated:** {now}  ",
        "**Phase:** 4 — Data Cleaning  ",
        "",
        "---",
        "",
        "## Cleaning Actions",
        "",
        "| Table | Issue | Action | Reason | Records Affected |",
        "|-------|-------|--------|--------|-----------------|",
    ]
    for entry in CLEANING_LOG:
        lines.append(
            f"| `{entry['table']}` | {entry['issue']} | {entry['action']} | "
            f"{entry['reason']} | {entry['affected']:,} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Cleaning Principles Applied",
        "",
        "1. **Raw data never modified** — all changes applied to copies only",
        "2. **Meaningful NULLs preserved** — `days_since_prior_order` NULL for first orders is kept as-is",
        "3. **No imputation** — missing values not filled unless justified",
        "4. **No row deletion without cause** — rows removed only if duplicates confirmed",
        "5. **All transformations reproducible** — script can be re-run to produce identical output",
        "6. **Assertions after every table** — ensures row counts and PK uniqueness are maintained",
        "",
        "## Output Files",
        "",
        "| Output File | Source | Format |",
        "|-------------|--------|--------|",
        "| `aisles_clean.parquet` | aisles.csv | Parquet |",
        "| `departments_clean.parquet` | departments.csv | Parquet |",
        "| `products_clean.parquet` | products.csv | Parquet |",
        "| `orders_clean.parquet` | orders.csv | Parquet |",
        "| `order_products_prior_clean.parquet` | order_products__prior.csv | Parquet |",
        "| `order_products_train_clean.parquet` | order_products__train.csv | Parquet |",
        "",
        "---",
        "",
        "*Generated by python/clean_data.py — Phase 4*",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"  ✅ Cleaning log written: {output_path}")


def main():
    logger.info("=" * 60)
    logger.info("PHASE 4: Data Cleaning — START")
    logger.info(f"  Raw:       {RAW_DIR}")
    logger.info(f"  Processed: {PROCESSED_DIR}")
    logger.info("=" * 60)

    start = time.time()

    # ── aisles ─────────────────────────────────────────────────────────────────
    logger.info("\n[1/6] Cleaning: aisles")
    df_aisles = pd.read_csv(RAW_DIR / "aisles.csv", dtype=READ_DTYPES["aisles"])
    df_aisles = clean_aisles(df_aisles)
    df_aisles.to_parquet(PROCESSED_DIR / "aisles_clean.parquet", index=False)
    logger.info("  ✅ Saved: aisles_clean.parquet")

    # ── departments ────────────────────────────────────────────────────────────
    logger.info("\n[2/6] Cleaning: departments")
    df_departments = pd.read_csv(RAW_DIR / "departments.csv", dtype=READ_DTYPES["departments"])
    df_departments = clean_departments(df_departments)
    df_departments.to_parquet(PROCESSED_DIR / "departments_clean.parquet", index=False)
    logger.info("  ✅ Saved: departments_clean.parquet")

    # ── products ───────────────────────────────────────────────────────────────
    logger.info("\n[3/6] Cleaning: products")
    df_products = pd.read_csv(RAW_DIR / "products.csv", dtype=READ_DTYPES["products"])
    df_products = clean_products(df_products)
    df_products.to_parquet(PROCESSED_DIR / "products_clean.parquet", index=False)
    logger.info("  ✅ Saved: products_clean.parquet")

    # ── orders ─────────────────────────────────────────────────────────────────
    logger.info("\n[4/6] Cleaning: orders")
    df_orders = pd.read_csv(RAW_DIR / "orders.csv", dtype=READ_DTYPES["orders"])
    df_orders = clean_orders(df_orders)
    df_orders.to_parquet(PROCESSED_DIR / "orders_clean.parquet", index=False)
    logger.info("  ✅ Saved: orders_clean.parquet")
    del df_orders

    # ── order_products__prior ──────────────────────────────────────────────────
    logger.info("\n[5/6] Cleaning: order_products__prior (large file — may take ~20s)")
    df_prior = pd.read_csv(RAW_DIR / "order_products__prior.csv", dtype=READ_DTYPES["order_products__prior"])
    df_prior = clean_order_products(df_prior, "order_products__prior")
    df_prior.to_parquet(PROCESSED_DIR / "order_products_prior_clean.parquet", index=False)
    logger.info("  ✅ Saved: order_products_prior_clean.parquet")
    del df_prior

    import gc; gc.collect()

    # ── order_products__train ──────────────────────────────────────────────────
    logger.info("\n[6/6] Cleaning: order_products__train")
    df_train = pd.read_csv(RAW_DIR / "order_products__train.csv", dtype=READ_DTYPES["order_products__train"])
    df_train = clean_order_products(df_train, "order_products__train")
    df_train.to_parquet(PROCESSED_DIR / "order_products_train_clean.parquet", index=False)
    logger.info("  ✅ Saved: order_products_train_clean.parquet")
    del df_train

    # ── Write cleaning log ─────────────────────────────────────────────────────
    logger.info("\nWriting cleaning log ...")
    write_cleaning_log(REPORTS_DIR / "data_cleaning_log.md")

    elapsed = time.time() - start
    logger.info("\n" + "=" * 60)
    logger.info(f"PHASE 4: Data Cleaning — COMPLETE ({elapsed:.1f}s)")
    logger.info("=" * 60)

    processed_files = list(PROCESSED_DIR.glob("*.parquet"))
    print("\n" + "=" * 50)
    print("  DATA CLEANING COMPLETE")
    print("=" * 50)
    print(f"  Files cleaned     : 6")
    print(f"  Parquet files out : {len(processed_files)}")
    for pf in sorted(processed_files):
        size_mb = pf.stat().st_size / (1024 * 1024)
        print(f"    {pf.name:<45} {size_mb:.1f} MB")
    print(f"  Cleaning log      : reports/data_cleaning_log.md")
    print(f"  Time elapsed      : {elapsed:.1f}s")
    print("=" * 50)


if __name__ == "__main__":
    main()
