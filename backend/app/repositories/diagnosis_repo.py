# repositories/diagnosis_repo.py
from psycopg2.extras import RealDictCursor
from ..pg_base import get_pg_conn


class DiagnosisRepository:
    """處理診斷（DIAGNOSIS）相關的資料庫操作"""

    @staticmethod
    def list_diagnoses_for_encounter(enct_id):
        """
        查詢一個就診紀錄的所有診斷。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        d.enct_id,
                        d.code_icd,
                        dis.description,
                        d.is_primary
                    FROM DIAGNOSIS d
                    JOIN DISEASE dis ON d.code_icd = dis.code_icd
                    WHERE d.enct_id = %s
                    ORDER BY d.is_primary DESC, d.code_icd;
                    """,
                    (enct_id,),
                )
                return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def upsert_diagnosis(enct_id, code_icd, is_primary):
        """
        新增或更新診斷（以 enct_id + code_icd 為 key）。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO DIAGNOSIS (enct_id, code_icd, is_primary)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (enct_id, code_icd)
                    DO UPDATE SET is_primary = EXCLUDED.is_primary;
                    """,
                    (enct_id, code_icd, is_primary),
                )
                conn.commit()
        finally:
            conn.close()

    @staticmethod
    def set_primary_diagnosis(enct_id, code_icd):
        """
        將某一個診斷標為主要診斷，同時把同一 enct_id 其他診斷 is_primary 設為 FALSE。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE DIAGNOSIS SET is_primary = FALSE WHERE enct_id = %s;",
                    (enct_id,),
                )
                cur.execute(
                    """
                    UPDATE DIAGNOSIS
                    SET is_primary = TRUE
                    WHERE enct_id = %s
                      AND code_icd = %s;
                    """,
                    (enct_id, code_icd),
                )
                conn.commit()
        finally:
            conn.close()

