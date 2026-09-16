"""
run_pipeline.py
===============
Enterprise Retail Intelligence & Decision Engine
Master Pipeline Runner

Executes all phases in order. Fails clearly if any stage fails.

Usage:
    python python/run_pipeline.py [--phase PHASE_NAME]

Phases:
    profile    — Phase 2: Dataset profiling
    clean      — Phase 4: Data cleaning
    validate   — Phase 5: Data validation
    load_db    — Phase 6: MySQL loading
    features   — Phase 9: Customer features
    segment    — Phase 10: Customer segmentation
    predict    — Phase 11: Reorder prediction
    basket     — Phase 12: Market basket analysis
    all        — Run all phases in order (default)
"""

import sys
import logging
import time
import subprocess
import argparse
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "pipeline.log", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON       = PROJECT_ROOT / ".venv" / "bin" / "python"

PHASES = {
    "profile":  PROJECT_ROOT / "python" / "profile_dataset.py",
    "clean":    PROJECT_ROOT / "python" / "clean_data.py",
    "validate": PROJECT_ROOT / "python" / "validate_data.py",
    "load_db":  PROJECT_ROOT / "python" / "load_mysql.py",
    "features": PROJECT_ROOT / "python" / "customer_features.py",
    "segment":  PROJECT_ROOT / "python" / "customer_segmentation.py",
    "predict":  PROJECT_ROOT / "python" / "reorder_prediction.py",
    "basket":   PROJECT_ROOT / "python" / "market_basket.py",
}


def run_phase(phase_name: str, script_path: Path) -> bool:
    """Run a pipeline phase. Returns True on success, False on failure."""
    logger.info(f"\n{'='*60}")
    logger.info(f"  RUNNING: {phase_name.upper()}")
    logger.info(f"  Script: {script_path.name}")
    logger.info(f"{'='*60}")

    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False

    t0 = time.time()
    result = subprocess.run(
        [str(PYTHON), str(script_path)],
        capture_output=False,
        cwd=str(PROJECT_ROOT),
    )
    elapsed = time.time() - t0

    if result.returncode == 0:
        logger.info(f"  ✅ {phase_name.upper()} PASSED ({elapsed:.1f}s)")
        return True
    else:
        logger.error(f"  ❌ {phase_name.upper()} FAILED (exit code {result.returncode}, {elapsed:.1f}s)")
        return False


def main():
    parser = argparse.ArgumentParser(description="Enterprise BI Pipeline Runner")
    parser.add_argument("--phase", default="all",
                        choices=list(PHASES.keys()) + ["all"],
                        help="Phase to run (default: all)")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("ENTERPRISE RETAIL INTELLIGENCE PIPELINE — START")
    logger.info(f"Phase: {args.phase}")
    logger.info("=" * 60)

    t_pipeline = time.time()
    results = {}

    phases_to_run = list(PHASES.items()) if args.phase == "all" else [(args.phase, PHASES[args.phase])]

    for phase_name, script_path in phases_to_run:
        success = run_phase(phase_name, script_path)
        results[phase_name] = success
        if not success:
            logger.error(f"\n❌ PIPELINE ABORTED at phase: {phase_name}")
            logger.error("Fix the error above and re-run.")
            sys.exit(1)

    total = time.time() - t_pipeline
    logger.info(f"\n{'='*60}")
    logger.info("PIPELINE COMPLETE")
    logger.info(f"{'='*60}")
    for phase, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"  {phase:<15} {status}")
    logger.info(f"\n  Total time: {total:.0f}s ({total/60:.1f} min)")


if __name__ == "__main__":
    main()
