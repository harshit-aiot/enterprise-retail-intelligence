"""
config.py — Application configuration and database connection settings.
Reads from .env file — never hard-codes credentials.
"""
import os
from pathlib import Path
from urllib.parse import quote_plus

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def load_env() -> dict:
    env_path = PROJECT_ROOT / ".env"
    env = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

_env = load_env()

MYSQL_HOST     = _env.get("MYSQL_HOST", "localhost")
MYSQL_PORT     = int(_env.get("MYSQL_PORT", "3306"))
MYSQL_DATABASE = _env.get("MYSQL_DATABASE", "enterprise_bi")
MYSQL_USER     = _env.get("MYSQL_USER", "root")
MYSQL_PASSWORD = _env.get("MYSQL_PASSWORD", "")

PROCESSED_DIR  = PROJECT_ROOT / "data" / "Processed"
REPORTS_DIR    = PROJECT_ROOT / "reports"

APP_TITLE      = "Enterprise Retail Intelligence & Decision Engine"
APP_ICON       = "🛒"
