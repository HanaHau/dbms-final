# repositories/encounter_repo.py
from psycopg2.extras import RealDictCursor
from ..pg_base import get_pg_conn


class EncounterRepository:
    """處理就診紀錄（ENCOUNTER）相關的資料庫操作"""

    @staticmethod
    def get_encounter_by_appt(provider_user_id, appt_id):
        """
        查詢某筆掛號對應的就診紀錄（只看自己的 encounter）。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        e.enct_id,
                        e.appt_id,
                        e.provider_id,
                        e.encounter_at,
                        e.status,
                        e.chief_complaint,
                        e.subjective,
                        e.assessment,
                        e.plan
                    FROM ENCOUNTER e
                    WHERE e.appt_id = %s
                      AND e.provider_id = %s;
                    """,
                    (appt_id, provider_user_id),
                )
                return cur.fetchone()
        finally:
            conn.close()

    @staticmethod
    def upsert_encounter(
        provider_user_id,
        appt_id,
        status,
        chief_complaint,
        subjective,
        assessment,
        plan,
    ):
        """
        新增或更新就診紀錄：
        - 若該 provider + appt 還沒有 ENCOUNTER，就插入一筆
        - 否則更新內容（支援草稿 / 定稿）
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT enct_id
                    FROM ENCOUNTER
                    WHERE appt_id = %s
                      AND provider_id = %s;
                    """,
                    (appt_id, provider_user_id),
                )
                row = cur.fetchone()

                if row is None:
                    cur.execute(
                        """
                        INSERT INTO ENCOUNTER (
                            appt_id, provider_id, encounter_at,
                            status, chief_complaint, subjective, assessment, plan
                        )
                        VALUES (%s, %s, NOW(),
                                %s, %s, %s, %s, %s)
                        RETURNING enct_id, appt_id, provider_id, encounter_at,
                                  status, chief_complaint, subjective, assessment, plan;
                        """,
                        (
                            appt_id,
                            provider_user_id,
                            status,
                            chief_complaint,
                            subjective,
                            assessment,
                            plan,
                        ),
                    )
                else:
                    enct_id = row["enct_id"]
                    cur.execute(
                        """
                        UPDATE ENCOUNTER
                        SET status          = %s,
                            chief_complaint = %s,
                            subjective      = %s,
                            assessment      = %s,
                            plan            = %s
                        WHERE enct_id = %s
                          AND provider_id = %s
                        RETURNING enct_id, appt_id, provider_id, encounter_at,
                                  status, chief_complaint, subjective, assessment, plan;
                        """,
                        (
                            status,
                            chief_complaint,
                            subjective,
                            assessment,
                            plan,
                            enct_id,
                            provider_user_id,
                        ),
                    )

                result = cur.fetchone()
                conn.commit()
                return result
        finally:
            conn.close()

    @staticmethod
    def list_encounters_for_patient(patient_id, provider_id=None):
        """
        查詢某位病人的所有就診紀錄。
        如果提供 provider_id，則只查詢該醫師的就診紀錄。
        包含：就診 ID、掛號資訊、門診時段資訊、醫師資訊等。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                conditions = ["a.patient_id = %s"]
                params = [patient_id]

                if provider_id is not None:
                    conditions.append("e.provider_id = %s")
                    params.append(provider_id)

                where_clause = " AND ".join(conditions)

                cur.execute(
                    f"""
                    SELECT
                        e.enct_id,
                        e.appt_id,
                        e.provider_id,
                        e.encounter_at,
                        e.status,
                        e.chief_complaint,
                        e.subjective,
                        e.assessment,
                        e.plan,
                        a.patient_id,
                        a.session_id,
                        cs.date AS session_date,
                        cs.start_time AS session_start_time,
                        cs.end_time AS session_end_time,
                        u_provider.name AS provider_name,
                        pr.dept_id,
                        d.name AS department_name
                    FROM ENCOUNTER e
                    JOIN APPOINTMENT a ON e.appt_id = a.appt_id
                    JOIN CLINIC_SESSION cs ON a.session_id = cs.session_id
                    JOIN PROVIDER pr ON e.provider_id = pr.user_id
                    JOIN "USER" u_provider ON pr.user_id = u_provider.user_id
                    LEFT JOIN DEPARTMENT d ON pr.dept_id = d.dept_id
                    WHERE {where_clause}
                    ORDER BY e.encounter_at DESC;
                    """,
                    params,
                )
                return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def list_encounters_for_patient_by_provider(provider_user_id, patient_user_id):
        """
        醫師查詢某位病患在「自己」這裡的所有就診紀錄，
        供完整病歷查詢與追蹤使用。
        （此方法為向後兼容，實際調用 list_encounters_for_patient）
        """
        return EncounterRepository.list_encounters_for_patient(
            patient_user_id, provider_id=provider_user_id
        )

