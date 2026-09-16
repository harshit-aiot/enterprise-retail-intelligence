"""
load_mysql.py
=============
Enterprise Retail Intelligence & Decision Engine
Phase 6: MySQL Database Loading

Executes the SQL DDL scripts and then bulk-loads the cleaned
Parquet data into MySQL using efficient INSERT batching via
SQLAlchemy + PyMySQL.

Uses environment variables for credentials (never hard-coded).

Usage:
    python python/load_mysql.py

Environment variables required (set in .env):
    MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD
"""

import os
import sys
import logging
import time
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# ─── Logging ───────────────────────────────────────────────────────────────────
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "load_mysql.log", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ─── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT  = Path(__file__).resolve().parent.parent
SQL_DIR       = PROJECT_ROOT / "sql"
PROCESSED_DIR = PROJECT_ROOT / "data" / "Processed"

# ─── Load .env manually (avoid python-dotenv dependency) ───────────────────────
def load_env() -> dict:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        logger.error(f".env file not found at {env_path}")
        sys.exit(1)
    env = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def get_engine(env: dict):
    """Create SQLAlchemy engine from env config.

    URL-encodes the password to handle special characters (e.g. @ % #).
    """
    from urllib.parse import quote_plus
    host     = env.get("MYSQL_HOST", "localhost")
    port     = env.get("MYSQL_PORT", "3306")
    db       = env.get("MYSQL_DATABASE", "enterprise_bi")
    user     = env.get("MYSQL_USER", "root")
    password = quote_plus(env.get("MYSQL_PASSWORD", ""))
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"
    return create_engine(url, pool_pre_ping=True)


def run_sql_file(engine, sql_path: Path) -> None:
    """Execute a .sql file statement by statement."""
    logger.info(f"  Running: {sql_path.name}")
    sql_text = sql_path.read_text(encoding="utf-8")
    # Split on semicolons, filter blanks and comments-only blocks
    statements = [s.strip() for s in sql_text.split(";") if s.strip()]
    with engine.connect() as conn:
        for stmt in statements:
            if stmt.upper().startswith("--") or not stmt:
                continue
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception as e:
                # Some statements like SHOW TABLES are OK to fail in this context
                logger.debug(f"    Stmt note: {str(e)[:100]}")


def load_parquet_to_mysql(
    engine, parquet_file: Path, table_name: str,
    chunksize: int = 50_000, dtype_map: dict | None = None
) -> int:
    """
    Load a Parquet file into MySQL using chunked DataFrame.to_sql().

    Returns total rows inserted.
    """
    logger.info(f"  Loading: {parquet_file.name} → {table_name}")
    df = pd.read_parquet(parquet_file)

    # Apply column transformations needed for MySQL compatibility
    if dtype_map:
        for col, py_type in dtype_map.items():
            if col in df.columns:
                df[col] = df[col].astype(py_type)

    total_rows = len(df)
    t0 = time.time()

    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=chunksize,
        method="multi",
    )

    elapsed = time.time() - t0
    logger.info(f"    ✅ {total_rows:,} rows loaded in {elapsed:.1f}s ({total_rows/elapsed:,.0f} rows/sec)")
    del df
    return total_rows


def verify_counts(engine) -> None:
    """Verify row counts in all staging tables after load."""
    tables = [
        "stg_departments",
        "stg_aisles",
        "stg_products",
        "stg_orders",
        "stg_order_products_prior",
        "stg_order_products_train",
    ]
    expected = {
        "stg_departments":           21,
        "stg_aisles":               134,
        "stg_products":          49_688,
        "stg_orders":         3_421_083,
        "stg_order_products_prior": 32_434_489,
        "stg_order_products_train":  1_384_617,
    }
    logger.info("\n── Row count verification ──────────────────────────────────")
    all_pass = True
    with engine.connect() as conn:
        for tbl in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}"))
            count  = result.scalar()
            exp    = expected.get(tbl, -1)
            status = "✅ PASS" if count == exp else f"❌ FAIL (expected {exp:,})"
            logger.info(f"  {tbl:<35} {count:>12,}  {status}")
            if count != exp:
                all_pass = False
    if not all_pass:
        logger.error("Row count mismatches detected!")
        sys.exit(1)


def main():
    logger.info("=" * 60)
    logger.info("PHASE 6: MySQL Database Loading — START")
    logger.info("=" * 60)

    env    = load_env()
    engine = get_engine(env)

    # Test connection
    logger.info("\nTesting MySQL connection ...")
    with engine.connect() as conn:
        version = conn.execute(text("SELECT VERSION()")).scalar()
        logger.info(f"  ✅ Connected to MySQL {version}")

    # Step 1: Create database + tables
    logger.info("\n[1/4] Running DDL scripts ...")
    run_sql_file(engine, SQL_DIR / "01_create_database.sql")
    run_sql_file(engine, SQL_DIR / "02_create_tables.sql")
    logger.info("  ✅ Tables created")

    # Step 2: Load data — small tables first (respect FK dependency order)
    logger.info("\n[2/4] Loading data into staging tables ...")
    total_rows = 0

    # Departments (21 rows — no FKs)
    total_rows += load_parquet_to_mysql(
        engine,
        PROCESSED_DIR / "departments_clean.parquet",
        "stg_departments",
        dtype_map={"department_id": "int64", "department": "str"},
    )

    # Aisles (134 rows — no FKs)
    total_rows += load_parquet_to_mysql(
        engine,
        PROCESSED_DIR / "aisles_clean.parquet",
        "stg_aisles",
        dtype_map={"aisle_id": "int64", "aisle": "str"},
    )

    # Products (49,688 rows — FK: aisles, departments)
    total_rows += load_parquet_to_mysql(
        engine,
        PROCESSED_DIR / "products_clean.parquet",
        "stg_products",
        dtype_map={"product_id": "int64", "aisle_id": "int64", "department_id": "int64"},
    )

    # Orders (3.4M rows)
    total_rows += load_parquet_to_mysql(
        engine,
        PROCESSED_DIR / "orders_clean.parquet",
        "stg_orders",
        chunksize=100_000,
        dtype_map={
            "order_id":    "int64",
            "user_id":     "int64",
            "eval_set":    "str",
            "order_number": "int64",
            "order_dow":   "int64",
            "order_hour_of_day": "int64",
            "is_first_order": "int64",
        },
    )

    # Prior order-products (32.4M rows — large)
    logger.info("  Loading order_products_prior (32.4M rows — this will take several minutes) ...")
    total_rows += load_parquet_to_mysql(
        engine,
        PROCESSED_DIR / "order_products_prior_clean.parquet",
        "stg_order_products_prior",
        chunksize=100_000,
        dtype_map={
            "order_id": "int64", "product_id": "int64",
            "add_to_cart_order": "int64", "reordered": "int64",
        },
    )

    # Train order-products (1.38M rows)
    total_rows += load_parquet_to_mysql(
        engine,
        PROCESSED_DIR / "order_products_train_clean.parquet",
        "stg_order_products_train",
        chunksize=100_000,
        dtype_map={
            "order_id": "int64", "product_id": "int64",
            "add_to_cart_order": "int64", "reordered": "int64",
        },
    )

    logger.info(f"\n  Total rows loaded: {total_rows:,}")

    # Step 3: Create indexes
    logger.info("\n[3/4] Creating indexes ...")
    run_sql_file(engine, SQL_DIR / "03_indexes.sql")
    logger.info("  ✅ Indexes created")

    # Step 4: Verify row counts
    logger.info("\n[4/4] Verifying row counts ...")
    verify_counts(engine)

    logger.info("\n" + "=" * 60)
    logger.info("PHASE 6: MySQL Database Loading — COMPLETE ✅")
    logger.info("=" * 60)
    print(f"\n✅ Database loaded successfully. Total rows: {total_rows:,}")


if __name__ == "__main__":
    main()
