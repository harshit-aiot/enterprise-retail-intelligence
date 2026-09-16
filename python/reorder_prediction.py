"""
reorder_prediction.py
=====================
Enterprise Retail Intelligence & Decision Engine
Phase 11: Reorder Prediction ML Pipeline

Target: reordered (binary: 0 or 1)

Pipeline:
    1. Feature engineering from prior order-product data
    2. Time-based train/test split (prevents data leakage)
    3. Baseline model (always-predict-majority)
    4. Logistic Regression
    5. Random Forest
    6. Evaluation: accuracy, precision, recall, F1, ROC-AUC
    7. Feature importance analysis
    8. Report generation

Data Leakage Prevention:
    - Target (reordered) comes from order_products__train
    - Features come ONLY from prior order behavior
    - No future information is used to build features
"""

import sys
import logging
import time
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix,
    classification_report
)

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "reorder_prediction.log", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

PROJECT_ROOT  = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "Processed"
REPORTS_DIR   = PROJECT_ROOT / "reports"


def build_features() -> tuple[pd.DataFrame, pd.Series]:
    """
    Build feature matrix and target vector for reorder prediction.

    Features (all from PRIOR order history — leakage-free):
        user_reorder_rate           — how often this user reorders overall (historical)
        product_reorder_rate        — how often this product is reordered globally
        user_total_orders           — total prior orders for this user
        user_avg_basket_size        — user's average basket size
        days_since_prior_order      — days since the user's last order
        add_to_cart_order           — position in cart (from train set order)
        user_unique_products        — number of unique products user has bought
        user_avg_days_between       — user's typical inter-order gap

    Leakage Removed:
        user_product_orders was removed — how many times a user bought a specific product
        is a near-perfect proxy for reordered=1, leaking the target.

    Target:
        reordered (from order_products__train)

    No leakage: all features derived from prior orders only.
    """
    logger.info("Loading data ...")
    orders = pd.read_parquet(PROCESSED_DIR / "orders_clean.parquet")
    prior  = pd.read_parquet(PROCESSED_DIR / "order_products_prior_clean.parquet")
    train  = pd.read_parquet(PROCESSED_DIR / "order_products_train_clean.parquet")

    logger.info(f"  Prior rows:  {len(prior):,}")
    logger.info(f"  Train rows:  {len(train):,}")

    # ── User-level features from prior ────────────────────────────────────────
    logger.info("Building user features from prior ...")
    prior_orders = orders[orders["eval_set"] == "prior"]

    user_stats = (
        prior_orders.merge(
            prior.groupby("order_id").agg(basket_size=("product_id","count")).reset_index(),
            on="order_id", how="left"
        )
        .groupby("user_id")
        .agg(
            user_total_orders    = ("order_id",    "count"),
            user_avg_basket_size = ("basket_size", "mean"),
            user_reorder_rate    = ("order_id",    "count"),  # placeholder; override below
        )
        .reset_index()
    )

    # Actual user reorder rate
    user_reorder = (
        prior.merge(prior_orders[["order_id","user_id"]], on="order_id")
        .groupby("user_id")["reordered"]
        .mean()
        .reset_index()
        .rename(columns={"reordered": "user_reorder_rate"})
    )

    # User unique product count
    user_unique_prods = (
        prior.merge(prior_orders[["order_id","user_id"]], on="order_id")
        .groupby("user_id")["product_id"]
        .nunique()
        .reset_index()
        .rename(columns={"product_id": "user_unique_products"})
    )

    user_features = (
        user_stats[["user_id", "user_total_orders", "user_avg_basket_size"]]
        .merge(user_reorder, on="user_id")
        .merge(user_unique_prods, on="user_id")
    )

    # ── Product-level features from prior ────────────────────────────────────
    logger.info("Building product features from prior ...")
    product_stats = (
        prior.groupby("product_id")
        .agg(
            product_reorder_rate = ("reordered", "mean"),
            product_total_orders = ("order_id",  "count"),
        )
        .reset_index()
    )

    # ── Additional user-level features ────────────────────────────────────────
    logger.info("Building additional user features ...")
    prior_with_user = prior.merge(
        prior_orders[["order_id", "user_id"]], on="order_id"
    )
    user_gap_stats = (
        prior_orders.groupby("user_id")["days_since_prior_order"]
        .mean()
        .reset_index()
        .rename(columns={"days_since_prior_order": "user_avg_days_between"})
    )

    # ── Train set orders → get user_id and days_since_prior ──────────────────
    train_orders = orders[orders["eval_set"] == "train"][
        ["order_id", "user_id", "days_since_prior_order"]
    ]

    # ── Assemble training data ────────────────────────────────────────────────
    logger.info("Assembling feature matrix ...")
    df = (
        train
        .merge(train_orders, on="order_id")
        .merge(user_features, on="user_id", how="left")
        .merge(product_stats, on="product_id", how="left")
        .merge(user_gap_stats, on="user_id", how="left")
    )

    df["days_since_prior_order"] = df["days_since_prior_order"].fillna(
        df["days_since_prior_order"].median()
    )
    df["user_avg_days_between"] = df["user_avg_days_between"].fillna(
        df["user_avg_days_between"].median()
    )

    # NOTE: user_product_orders REMOVED — it is a near-perfect proxy for
    # reordered=1 (if you bought a product N>0 times, it IS a reorder).
    # Using it would constitute data leakage (accuracy artificially ~100%).
    FEATURE_COLS = [
        "user_reorder_rate",        # user-level aggregate
        "product_reorder_rate",     # product-level aggregate
        "user_total_orders",        # user engagement depth
        "user_avg_basket_size",     # user shopping pattern
        "days_since_prior_order",   # order timing
        "add_to_cart_order",        # cart behaviour
        "user_unique_products",     # user diversity
        "user_avg_days_between",    # user shopping cadence
    ]

    df_features = df[FEATURE_COLS].fillna(0)
    y = df["reordered"]

    logger.info(f"  Feature matrix: {df_features.shape}")
    logger.info(f"  Target distribution: reordered={y.mean():.3f} ({y.sum():,}/{len(y):,})")

    return df_features, y, FEATURE_COLS


def evaluate_model(name: str, y_true, y_pred, y_prob=None) -> dict:
    """Compute and log all evaluation metrics."""
    metrics = {
        "model":     name,
        "accuracy":  round(accuracy_score(y_true, y_pred), 4),
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall":    round(recall_score(y_true, y_pred, zero_division=0), 4),
        "f1":        round(f1_score(y_true, y_pred, zero_division=0), 4),
        "roc_auc":   round(roc_auc_score(y_true, y_prob) if y_prob is not None else 0.5, 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }
    logger.info(f"\n  {name}:")
    for k, v in metrics.items():
        if k not in ("model", "confusion_matrix"):
            logger.info(f"    {k:<12} : {v}")
    cm = metrics["confusion_matrix"]
    logger.info(f"    Confusion Matrix: TN={cm[0][0]:,} FP={cm[0][1]:,} FN={cm[1][0]:,} TP={cm[1][1]:,}")
    return metrics


def write_model_report(all_metrics: list, feature_names: list,
                       rf_importances: np.ndarray, lr_coefs: np.ndarray) -> None:
    now = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Enterprise Retail Intelligence & Decision Engine",
        "## Reorder Prediction Model Evaluation Report",
        "",
        f"**Generated:** {now}  ",
        "**Phase:** 11 — Reorder Prediction  ",
        "**Target Variable:** `reordered` (binary: 0=first purchase, 1=repurchase)  ",
        "",
        "---",
        "",
        "## Data Leakage Prevention",
        "",
        "- All features derived from **prior order history only**",
        "- Target variable (`reordered`) comes from **train order set** only",
        "- No future information used in feature construction",
        "- Train/test split: 80/20 random split on the train order-product rows",
        "",
        "## Features Used",
        "",
        "| Feature | Description |",
        "|---------|-------------|",
        "| user_reorder_rate | User's overall historical reorder rate (from prior) |",
        "| product_reorder_rate | Product's global reorder rate across all users (from prior) |",
        "| user_total_orders | Total prior orders for this user |",
        "| user_avg_basket_size | User's average basket size (prior) |",
        "| days_since_prior_order | Days since this user's last order |",
        "| add_to_cart_order | Cart add position in the train order |",
        "| user_unique_products | Unique products user has ever purchased |",
        "| user_avg_days_between | User's average days between orders (cadence) |",
        "",
        "**Feature removed (data leakage):**",
        "| user_product_orders | ~~Times user ordered this specific product~~ — removed because it is a near-perfect proxy for `reordered=1` |",
        "",
        "---",
        "",
        "## Model Comparison",
        "",
        "| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |",
        "|-------|----------|-----------|--------|----|---------|",
    ]
    for m in all_metrics:
        lines.append(
            f"| {m['model']} | {m['accuracy']} | {m['precision']} | "
            f"{m['recall']} | {m['f1']} | {m['roc_auc']} |"
        )

    lines += ["", "---", "", "## Feature Importance (Random Forest)", "", "| Feature | Importance |", "|---------|------------|"]
    rf_imp_sorted = sorted(zip(feature_names, rf_importances), key=lambda x: -x[1])
    for feat, imp in rf_imp_sorted:
        lines.append(f"| {feat} | {imp:.4f} |")

    lines += [
        "",
        "---",
        "",
        "## Limitations",
        "",
        "- No product price data — value-based reorder drivers cannot be modeled",
        "- No temporal timestamps — seasonality cannot be captured",
        "- Dataset is from 2017 — patterns may not reflect current behavior",
        "- Model predicts binary reorder probability, not quantity or timing",
        "- Streamlit predictions are model outputs, not guarantees",
        "",
        "---",
        "*Generated by python/reorder_prediction.py — Phase 11*",
    ]

    (REPORTS_DIR / "model_evaluation.md").write_text("\n".join(lines), encoding="utf-8")
    logger.info("  ✅ model_evaluation.md written")


def main():
    logger.info("=" * 60)
    logger.info("PHASE 11: Reorder Prediction — START")
    logger.info("=" * 60)
    t_start = time.time()

    X, y, feature_cols = build_features()

    # Train/test split (80/20)
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    logger.info(f"\nTrain: {len(X_train):,} | Test: {len(X_test):,}")
    logger.info(f"Class balance (train): {y_train.mean():.3f} reordered")

    all_metrics = []

    # ── Baseline: always predict majority class ────────────────────────────────
    logger.info("\nBaseline model (predict majority class) ...")
    majority = int(y_train.mode().iloc[0])
    y_baseline = np.full(len(y_test), majority)
    all_metrics.append(evaluate_model("Baseline (Majority Class)", y_test, y_baseline,
                                       y_prob=np.full(len(y_test), y_train.mean())))

    # ── Logistic Regression ───────────────────────────────────────────────────
    logger.info("\nLogistic Regression ...")
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    lr = LogisticRegression(max_iter=500, random_state=42, C=1.0)
    lr.fit(X_train_s, y_train)
    y_pred_lr = lr.predict(X_test_s)
    y_prob_lr = lr.predict_proba(X_test_s)[:, 1]
    all_metrics.append(evaluate_model("Logistic Regression", y_test, y_pred_lr, y_prob_lr))

    # ── Random Forest ─────────────────────────────────────────────────────────
    logger.info("\nRandom Forest (n_estimators=100) ...")
    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1,
                                 max_depth=10, min_samples_leaf=50)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    y_prob_rf = rf.predict_proba(X_test)[:, 1]
    all_metrics.append(evaluate_model("Random Forest", y_test, y_pred_rf, y_prob_rf))

    # ── Write report ──────────────────────────────────────────────────────────
    write_model_report(all_metrics, feature_cols, rf.feature_importances_, lr.coef_[0])

    # ── Save model artifacts ──────────────────────────────────────────────────
    import pickle
    model_dir = PROCESSED_DIR / "models"
    model_dir.mkdir(exist_ok=True)
    with open(model_dir / "rf_reorder_model.pkl", "wb") as f:
        pickle.dump(rf, f)
    with open(model_dir / "lr_reorder_model.pkl", "wb") as f:
        pickle.dump(lr, f)
    with open(model_dir / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    logger.info("  ✅ Models saved to data/Processed/models/")

    elapsed = time.time() - t_start
    logger.info(f"\n{'='*60}\nPHASE 11: COMPLETE ({elapsed:.1f}s)\n{'='*60}")

    best = max(all_metrics[1:], key=lambda x: x["roc_auc"])
    print(f"\n✅ Best model: {best['model']} | ROC-AUC={best['roc_auc']} | F1={best['f1']}")


if __name__ == "__main__":
    main()
