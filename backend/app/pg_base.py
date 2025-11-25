# pg_base.py
import psycopg2
from .config import PG_DSN


def get_pg_conn():
    """
    建立並返回一個 PostgreSQL 連接物件。
    """
    return psycopg2.connect(PG_DSN)

