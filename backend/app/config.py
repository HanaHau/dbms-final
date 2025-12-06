# config.py
import os
from dotenv import load_dotenv
from datetime import datetime, date, time

# 載入 .env
load_dotenv()

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB   = os.getenv("PG_DB", "dbms")
PG_USER = os.getenv("PG_USER", "hannah")
PG_PWD  = os.getenv("PG_PASSWORD", "")

# psycopg2 用的 DSN
PG_DSN = (
    f"dbname={PG_DB} user={PG_USER} password={PG_PWD} "
    f"host={PG_HOST} port={PG_PORT}"
)

# DuckDB postgres_scanner 用的 URI
PG_URI = f"postgresql://{PG_USER}:{PG_PWD}@{PG_HOST}:{PG_PORT}/{PG_DB}"

# 固定當前時間（用於開發/測試）
# 設定為 2025-12-07 14:30
FIXED_CURRENT_DATETIME = datetime(2025, 12, 7, 14, 30, 0)
FIXED_CURRENT_DATE = date(2025, 12, 7)
FIXED_CURRENT_TIME = time(14, 30, 0)

def get_current_datetime() -> datetime:
    """取得當前時間（如果設定了固定時間則返回固定時間）"""
    return FIXED_CURRENT_DATETIME

def get_current_date() -> date:
    """取得當前日期（如果設定了固定時間則返回固定日期）"""
    return FIXED_CURRENT_DATE

def get_current_time() -> time:
    """取得當前時間（如果設定了固定時間則返回固定時間）"""
    return FIXED_CURRENT_TIME
