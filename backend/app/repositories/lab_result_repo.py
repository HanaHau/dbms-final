# repositories/lab_result_repo.py
from psycopg2.extras import RealDictCursor
from ..pg_base import get_pg_conn


class LabResultRepository:
    """處理檢驗結果（LAB_RESULT）相關的資料庫操作"""

    @staticmethod
    def list_lab_results_for_encounter(enct_id):
        """
        查詢某次就診的所有檢驗結果。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        lab_id,
                        enct_id,
                        loinc_code,
                        item_name,
                        value,
                        unit,
                        ref_low,
                        ref_high,
                        abnormal_flag,
                        reported_at
                    FROM LAB_RESULT
                    WHERE enct_id = %s
                    ORDER BY reported_at NULLS LAST, lab_id;
                    """,
                    (enct_id,),
                )
                return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def list_lab_results_for_patient(patient_id):
        """
        查詢某位病人的所有檢驗結果。
        包含：檢驗 ID、就診 ID、檢驗項目、數值等。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        lab.lab_id,
                        lab.enct_id,
                        lab.loinc_code,
                        lab.item_name,
                        lab.value,
                        lab.unit,
                        lab.ref_low,
                        lab.ref_high,
                        lab.abnormal_flag,
                        lab.reported_at,
                        e.encounter_at,
                        e.provider_id,
                        u_provider.name AS provider_name,
                        pr.dept_id,
                        d.name AS department_name
                    FROM LAB_RESULT lab
                    JOIN ENCOUNTER e ON lab.enct_id = e.enct_id
                    JOIN APPOINTMENT a ON e.appt_id = a.appt_id
                    JOIN PROVIDER pr ON e.provider_id = pr.user_id
                    JOIN "USER" u_provider ON pr.user_id = u_provider.user_id
                    LEFT JOIN DEPARTMENT d ON pr.dept_id = d.dept_id
                    WHERE a.patient_id = %s
                    ORDER BY e.encounter_at DESC, lab.reported_at NULLS LAST, lab.lab_id;
                    """,
                    (patient_id,),
                )
                return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def add_lab_result(
        enct_id,
        loinc_code,
        item_name,
        value,
        unit,
        ref_low,
        ref_high,
        abnormal_flag,
        reported_at,
    ):
        """
        新增一筆檢驗結果。
        abnormal_flag: 'H' (高), 'L' (低), 'N' (正常), None
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO LAB_RESULT (
                        enct_id, loinc_code, item_name,
                        value, unit, ref_low, ref_high, abnormal_flag, reported_at
                    )
                    VALUES (%s, %s, %s,
                            %s, %s, %s, %s, %s, %s)
                    RETURNING lab_id, enct_id, loinc_code, item_name,
                              value, unit, ref_low, ref_high, abnormal_flag, reported_at;
                    """,
                    (
                        enct_id,
                        loinc_code,
                        item_name,
                        value,
                        unit,
                        ref_low,
                        ref_high,
                        abnormal_flag,
                        reported_at,
                    ),
                )
                conn.commit()
                return cur.fetchone()
        finally:
            conn.close()

