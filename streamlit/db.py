"""
db.py — Database connection layer using SQLAlchemy + PyMySQL.
"""
import streamlit as st
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD

@st.cache_resource
def get_engine():
    """Create and cache the SQLAlchemy engine."""
    password = quote_plus(MYSQL_PASSWORD)
    url = f"mysql+pymysql://{MYSQL_USER}:{password}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600)

def run_query(sql: str, params: dict | None = None):
    """Execute a SQL query and return a DataFrame."""
    import pandas as pd
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)

def test_connection() -> bool:
    """Test DB connectivity. Returns True/False."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
