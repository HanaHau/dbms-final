# pg_base.py
import psycopg2
from .config import PG_DSN


def get_pg_conn():
    """
    建立並返回一個 PostgreSQL 連接物件。
    """
    return psycopg2.connect(PG_DSN)


def generate_new_id(conn, table_name, id_column):
    """
    為指定的表和 ID 欄位生成一個新的 ID。
    
    Args:
        conn: psycopg2 連接物件
        table_name: 表名（可能需要引號，如 '"USER"'）
        id_column: ID 欄位名稱
    
    Returns:
        新的 ID（整數）
    """
    with conn.cursor() as cur:
        # 查詢該表的最大 ID
        cur.execute(f'SELECT COALESCE(MAX({id_column}), 0) FROM {table_name};')
        max_id = cur.fetchone()[0]
        return max_id + 1

