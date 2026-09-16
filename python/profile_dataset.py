"""
profile_dataset.py
==================
Enterprise Retail Intelligence & Decision Engine
Phase 2: Dataset Profiling

Inspects all six Instacart CSV files and generates:
  - reports/data_profile.md
  - reports/data_quality_report.md

Usage:
    Activate .venv first, then:
    python python/profile_dataset.py

Author: Enterprise BI Project
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# ─── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR      = PROJECT_ROOT / "data" / "Raw"
REPORTS_DIR  = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

CSV_FILES = {
    "aisles":                    RAW_DIR / "aisles.csv",
    "departments":               RAW_DIR / "departments.csv",
    "products":                  RAW_DIR / "products.csv",
    "orders":                    RAW_DIR / "orders.csv",
    "order_products__prior":     RAW_DIR / "order_products__prior.csv",
    "order_products__train":     RAW_DIR / "order_products__train.csv",
}

# ─── Efficient dtypes to reduce memory while profiling ─────────────────────────
DTYPES = {
    "aisles": {
        "aisle_id": "int16",
        "aisle":    "category",
    },
    "departments": {
        "department_id": "int8",
        "department":    "category",
    },
    "products": {
        "product_id":    "int32",
        "product_name":  "object",
        "aisle_id":      "int16",
        "department_id": "int8",
    },
    "orders": {
        "order_id":             "int32",
        "user_id":              "int32",
        "eval_set":             "category",
        "order_number":         "int16",
        "order_dow":            "int8",
        "order_hour_of_day":    "int8",
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


def get_file_size_mb(path: Path) -> float:
    """Return file size in MB."""
    return path.stat().st_size / (1024 * 1024)


def profile_dataframe(name: str, df: pd.DataFrame, file_path: Path) -> dict:
    """
    Generate a comprehensive profile of a single DataFrame.

    Returns a dict with all profiling metrics.
    """
    logger.info(f"  Profiling: {name} ({len(df):,} rows)")

    profile = {
        "name":           name,
        "file_path":      str(file_path),
        "file_size_mb":   round(get_file_size_mb(file_path), 2),
        "n_rows":         len(df),
        "n_cols":         len(df.columns),
        "columns":        list(df.columns),
        "dtypes":         {col: str(dtype) for col, dtype in df.dtypes.items()},
        "memory_mb":      round(df.memory_usage(deep=True).sum() / (1024 * 1024), 3),
        "missing":        {},
        "missing_pct":    {},
        "duplicates":     {},
        "unique_counts":  {},
        "numeric_stats":  {},
        "categorical":    {},
    }

    # Missing values per column
    for col in df.columns:
        n_missing = int(df[col].isna().sum())
        pct       = round(100 * n_missing / len(df), 4) if len(df) > 0 else 0.0
        profile["missing"][col]     = n_missing
        profile["missing_pct"][col] = pct

    # Duplicate rows (full row)
    profile["duplicates"]["full_row_duplicates"] = int(df.duplicated().sum())

    # Unique counts per column
    for col in df.columns:
        profile["unique_counts"][col] = int(df[col].nunique(dropna=False))

    # Numeric column statistics
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    for col in numeric_cols:
        s = df[col].dropna()
        profile["numeric_stats"][col] = {
            "min":    float(s.min()) if len(s) > 0 else None,
            "max":    float(s.max()) if len(s) > 0 else None,
            "mean":   round(float(s.mean()), 4) if len(s) > 0 else None,
            "median": round(float(s.median()), 4) if len(s) > 0 else None,
            "std":    round(float(s.std()), 4) if len(s) > 0 else None,
            "q25":    round(float(s.quantile(0.25)), 4) if len(s) > 0 else None,
            "q75":    round(float(s.quantile(0.75)), 4) if len(s) > 0 else None,
        }

    # Categorical columns — top values
    cat_cols = df.select_dtypes(include=["category", "object"]).columns.tolist()
    for col in cat_cols:
        top = df[col].value_counts(dropna=False).head(5).to_dict()
        profile["categorical"][col] = {str(k): int(v) for k, v in top.items()}

    return profile


def check_id_uniqueness(name: str, df: pd.DataFrame) -> dict:
    """Check primary key uniqueness for tables that have obvious PKs."""
    results = {}
    pk_map = {
        "aisles":                 ["aisle_id"],
        "departments":            ["department_id"],
        "products":               ["product_id"],
        "orders":                 ["order_id"],
        "order_products__prior":  ["order_id", "product_id"],
        "order_products__train":  ["order_id", "product_id"],
    }
    if name in pk_map:
        pk_cols = pk_map[name]
        available = [c for c in pk_cols if c in df.columns]
        if available:
            dups = int(df.duplicated(subset=available).sum())
            results["pk_columns"]   = available
            results["pk_dups"]      = dups
            results["pk_is_unique"] = dups == 0
    return results


def check_referential_integrity(
    profiles: dict, dfs: dict
) -> list:
    """
    Check FK relationships between tables.
    Returns a list of check result dicts.
    """
    checks = []

    def fk_check(child_name, child_col, parent_name, parent_col):
        if child_name not in dfs or parent_name not in dfs:
            return
        child_vals  = set(dfs[child_name][child_col].dropna().unique())
        parent_vals = set(dfs[parent_name][parent_col].dropna().unique())
        orphans     = child_vals - parent_vals
        checks.append({
            "child":        child_name,
            "child_col":    child_col,
            "parent":       parent_name,
            "parent_col":   parent_col,
            "child_unique": len(child_vals),
            "parent_unique": len(parent_vals),
            "orphan_values": len(orphans),
            "status":       "PASS" if len(orphans) == 0 else "FAIL",
        })

    fk_check("products",              "aisle_id",      "aisles",      "aisle_id")
    fk_check("products",              "department_id",  "departments", "department_id")
    fk_check("order_products__prior", "order_id",      "orders",      "order_id")
    fk_check("order_products__prior", "product_id",    "products",    "product_id")
    fk_check("order_products__train", "order_id",      "orders",      "order_id")
    fk_check("order_products__train", "product_id",    "products",    "product_id")

    return checks


def write_data_profile_md(profiles: dict, fk_checks: list, pk_results: dict) -> Path:
    """Write the detailed data_profile.md report."""
    out_path = REPORTS_DIR / "data_profile.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Enterprise Retail Intelligence & Decision Engine",
        "## Data Profile Report",
        "",
        f"**Generated:** {now}  ",
        "**Phase:** 2 — Dataset Profiling  ",
        "",
        "---",
        "",
    ]

    for name, p in profiles.items():
        lines += [
            f"## Table: `{name}`",
            "",
            f"| Property          | Value |",
            f"|-------------------|-------|",
            f"| File              | `{Path(p['file_path']).name}` |",
            f"| File Size         | {p['file_size_mb']} MB |",
            f"| Rows              | {p['n_rows']:,} |",
            f"| Columns           | {p['n_cols']} |",
            f"| Memory (in RAM)   | {p['memory_mb']} MB |",
            f"| Full-row Dupes    | {p['duplicates']['full_row_duplicates']:,} |",
            "",
            "### Columns & Data Types",
            "",
            "| Column | dtype | Missing | Missing % | Unique Values |",
            "|--------|-------|---------|-----------|---------------|",
        ]
        for col in p["columns"]:
            lines.append(
                f"| `{col}` | {p['dtypes'][col]} | "
                f"{p['missing'][col]:,} | {p['missing_pct'][col]:.2f}% | "
                f"{p['unique_counts'][col]:,} |"
            )

        if p["numeric_stats"]:
            lines += [
                "",
                "### Numeric Statistics",
                "",
                "| Column | Min | Max | Mean | Median | Std | Q25 | Q75 |",
                "|--------|-----|-----|------|--------|-----|-----|-----|",
            ]
            for col, stats in p["numeric_stats"].items():
                lines.append(
                    f"| `{col}` | {stats['min']} | {stats['max']} | "
                    f"{stats['mean']} | {stats['median']} | {stats['std']} | "
                    f"{stats['q25']} | {stats['q75']} |"
                )

        if p["categorical"]:
            lines += ["", "### Categorical Top Values", ""]
            for col, top in p["categorical"].items():
                lines.append(f"**`{col}`:** " + ", ".join(f"`{k}` ({v:,})" for k, v in top.items()))
            lines.append("")

        # PK results
        if name in pk_results:
            pk = pk_results[name]
            status = "✅ UNIQUE" if pk.get("pk_is_unique") else "❌ DUPLICATES FOUND"
            lines += [
                "### Primary Key Check",
                "",
                f"| PK Column(s) | Duplicate Count | Status |",
                f"|---|---|---|",
                f"| `{'`, `'.join(pk['pk_columns'])}` | {pk['pk_dups']:,} | {status} |",
                "",
            ]

        lines += ["---", ""]

    # FK checks
    lines += [
        "## Referential Integrity Checks",
        "",
        "| Child Table | FK Column | Parent Table | Parent Column | Orphan Values | Status |",
        "|-------------|-----------|--------------|---------------|---------------|--------|",
    ]
    for chk in fk_checks:
        lines.append(
            f"| `{chk['child']}` | `{chk['child_col']}` | `{chk['parent']}` | "
            f"`{chk['parent_col']}` | {chk['orphan_values']:,} | {chk['status']} |"
        )

    lines += ["", "---", "", "*Report generated by python/profile_dataset.py — Phase 2*", ""]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def write_data_quality_report_md(profiles: dict, fk_checks: list, pk_results: dict) -> Path:
    """Write the summary data_quality_report.md."""
    out_path = REPORTS_DIR / "data_quality_report.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total_missing   = sum(sum(p["missing"].values()) for p in profiles.values())
    total_fk_fails  = sum(1 for c in fk_checks if c["status"] == "FAIL")
    total_pk_fails  = sum(1 for p in pk_results.values() if not p.get("pk_is_unique", True))

    lines = [
        "# Enterprise Retail Intelligence & Decision Engine",
        "## Data Quality Report",
        "",
        f"**Generated:** {now}  ",
        "**Phase:** 2 — Dataset Profiling  ",
        "",
        "---",
        "",
        "## Summary Table",
        "",
        "| File | Rows | Columns | Missing Values | Duplicates | Memory (MB) | PK Unique | FK Issues | Notes |",
        "|------|------|---------|----------------|------------|-------------|-----------|-----------|-------|",
    ]

    for name, p in profiles.items():
        total_miss = sum(p["missing"].values())
        dupes      = p["duplicates"]["full_row_duplicates"]
        pk         = pk_results.get(name, {})
        pk_status  = "✅" if pk.get("pk_is_unique", True) else "❌"
        fk_issues  = [c for c in fk_checks if c["child"] == name and c["status"] == "FAIL"]
        fk_status  = f"✅ ({len([c for c in fk_checks if c['child']==name])} checked)" \
                     if not fk_issues else f"❌ ({len(fk_issues)} failed)"

        notes = []
        if name == "orders" and "days_since_prior_order" in p["missing"]:
            if p["missing"]["days_since_prior_order"] > 0:
                notes.append("1st orders have null days_since_prior (expected)")
        note_str = "; ".join(notes) if notes else "—"

        lines.append(
            f"| `{name}` | {p['n_rows']:,} | {p['n_cols']} | "
            f"{total_miss:,} | {dupes:,} | {p['memory_mb']} | "
            f"{pk_status} | {fk_status} | {note_str} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Overall Data Quality Assessment",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Missing Values (all tables) | {total_missing:,} |",
        f"| FK Integrity Failures | {total_fk_fails} |",
        f"| PK Uniqueness Failures | {total_pk_fails} |",
        "",
        "## Missing Value Analysis",
        "",
        "| Table | Column | Missing Count | Missing % | Business Explanation |",
        "|-------|--------|---------------|-----------|----------------------|",
    ]

    for name, p in profiles.items():
        for col, cnt in p["missing"].items():
            if cnt > 0:
                explanation = "—"
                if col == "days_since_prior_order":
                    explanation = "First order per user has no prior — expected, meaningful null"
                lines.append(
                    f"| `{name}` | `{col}` | {cnt:,} | {p['missing_pct'][col]:.2f}% | {explanation} |"
                )

    lines += [
        "",
        "---",
        "",
        "## Referential Integrity Detail",
        "",
        "| Child Table | FK Column | Parent | Parent Column | Orphans | Status |",
        "|-------------|-----------|--------|---------------|---------|--------|",
    ]
    for chk in fk_checks:
        lines.append(
            f"| `{chk['child']}` | `{chk['child_col']}` | `{chk['parent']}` | "
            f"`{chk['parent_col']}` | {chk['orphan_values']:,} | {chk['status']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Data Limitations (Confirmed — Not in Dataset)",
        "",
        "- Revenue / Product Price",
        "- Customer Demographics",
        "- Geographic Location",
        "- Inventory Levels",
        "- Actual Timestamps (only day-of-week and hour available)",
        "",
        "---",
        "",
        "*Report generated by python/profile_dataset.py — Phase 2*",
        "",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main():
    logger.info("=" * 60)
    logger.info("PHASE 2: Dataset Profiling — START")
    logger.info("=" * 60)

    # Verify all files exist
    for name, path in CSV_FILES.items():
        if not path.exists():
            logger.error(f"CRITICAL: File not found: {path}")
            sys.exit(1)
        logger.info(f"  ✅ Found: {path.name} ({get_file_size_mb(path):.1f} MB)")

    profiles  = {}
    dfs       = {}
    pk_results = {}

    for name, path in CSV_FILES.items():
        logger.info(f"\nLoading: {name} ...")
        t0 = time.time()

        dtypes = DTYPES.get(name, {})
        df = pd.read_csv(path, dtype=dtypes, low_memory=False)
        elapsed = time.time() - t0
        logger.info(f"  Loaded {len(df):,} rows in {elapsed:.1f}s")

        profile = profile_dataframe(name, df, path)
        pk      = check_id_uniqueness(name, df)

        profiles[name]   = profile
        pk_results[name] = pk
        dfs[name]        = df

        logger.info(f"  Memory: {profile['memory_mb']} MB | Missing: {sum(profile['missing'].values()):,}")
        if pk:
            status = "✅ UNIQUE" if pk.get("pk_is_unique") else f"❌ {pk['pk_dups']:,} DUPES"
            logger.info(f"  PK ({', '.join(pk['pk_columns'])}): {status}")

    logger.info("\nChecking referential integrity ...")
    fk_checks = check_referential_integrity(profiles, dfs)
    for chk in fk_checks:
        logger.info(
            f"  FK {chk['child']}.{chk['child_col']} → "
            f"{chk['parent']}.{chk['parent_col']}: {chk['status']} "
            f"(orphans: {chk['orphan_values']:,})"
        )

    # Free large DataFrames from memory before writing reports
    del dfs
    import gc; gc.collect()

    logger.info("\nWriting reports ...")
    p1 = write_data_profile_md(profiles, fk_checks, pk_results)
    logger.info(f"  ✅ Written: {p1}")

    p2 = write_data_quality_report_md(profiles, fk_checks, pk_results)
    logger.info(f"  ✅ Written: {p2}")

    logger.info("\n" + "=" * 60)
    logger.info("PHASE 2: Dataset Profiling — COMPLETE")
    logger.info("=" * 60)

    # Summary
    total_rows = sum(p["n_rows"] for p in profiles.values())
    total_miss = sum(sum(p["missing"].values()) for p in profiles.values())
    fk_fails   = sum(1 for c in fk_checks if c["status"] == "FAIL")
    pk_fails   = sum(1 for r in pk_results.values() if not r.get("pk_is_unique", True))

    print("\n" + "=" * 50)
    print("  PROFILING COMPLETE")
    print("=" * 50)
    print(f"  Tables profiled : {len(profiles)}")
    print(f"  Total rows      : {total_rows:,}")
    print(f"  Missing values  : {total_miss:,}")
    print(f"  FK check fails  : {fk_fails}")
    print(f"  PK uniqueness   : {'ALL PASS' if pk_fails == 0 else f'{pk_fails} FAILED'}")
    print(f"  Reports written : reports/data_profile.md")
    print(f"                    reports/data_quality_report.md")
    print("=" * 50)


if __name__ == "__main__":
    main()
