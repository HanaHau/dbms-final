# config.py
import os
from dotenv import load_dotenv

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
