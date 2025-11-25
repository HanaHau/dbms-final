# db_duck.py
import duckdb
from .config import PG_URI

DUCKDB_FILE = "clinic_analytics.duckdb"


def get_duckdb_conn():
    con = duckdb.connect(DUCKDB_FILE)
    # 啟用 postgres_scanner extension
    con.execute("INSTALL postgres_scanner")
    con.execute("LOAD postgres_scanner")
    # 把 PostgreSQL 附掛成 pgdb
    con.execute(f"ATTACH '{PG_URI}' AS pgdb (TYPE POSTGRES)")
    return con


def get_daily_encounter_stats():
    """
    例子：統計每天各醫師的看診次數
    以 ENCOUNTER 為主。
    """
    con = get_duckdb_conn()
    query = """
        SELECT
            date(e.encounter_at) AS visit_date,
            pr.user_id           AS provider_id,
            u_doc.name           AS provider_name,
            COUNT(*)             AS encounter_count
        FROM pgdb.public.ENCOUNTER e
        JOIN pgdb.public.PROVIDER pr ON e.provider_id = pr.user_id
        JOIN pgdb.public."USER" u_doc ON pr.user_id = u_doc.user_id
        GROUP BY visit_date, provider_id, provider_name
        ORDER BY visit_date DESC, provider_name;
    """
    return con.execute(query).df()
