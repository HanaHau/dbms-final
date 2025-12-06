# pg_base.py
import psycopg2
from .config import PG_DSN


def get_pg_conn():
    """
    建立並返回一個 PostgreSQL 連接物件。
    注意：如果需要在查詢中使用固定時間，請使用 app_current_date()、app_current_time() 和 app_now()
    而不是 CURRENT_DATE、CURRENT_TIME 和 NOW()
    """
    return psycopg2.connect(PG_DSN)

