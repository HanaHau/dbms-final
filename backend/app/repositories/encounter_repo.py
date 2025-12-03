# repositories/encounter_repo.py
from psycopg2.extras import RealDictCursor
from ..pg_base import get_pg_conn
from .appointment_repo import AppointmentRepository
from .session_repo import SessionRepository


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
                        e.plan,
                        a.patient_id
                    FROM ENCOUNTER e
                    JOIN APPOINTMENT a ON e.appt_id = a.appt_id
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
            # 確保使用事務
            conn.autocommit = False
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 先檢查 appt_id 是否存在（因為 appt_id 有唯一約束）
                cur.execute(
                    """
                    SELECT enct_id, provider_id
                    FROM ENCOUNTER
                    WHERE appt_id = %s;
                    """,
                    (appt_id,),
                )
                row = cur.fetchone()

                if row is None:
                    # 創建新的 encounter
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
                    
                    # 當創建 encounter 時，自動將 appointment 狀態更新為 completed (3)
                    # 根據資料字典：狀態定義 {1:booked, 2:checked_in, 3:completed, 4:cancelled, 5:no_show, 6:waitlisted}
                    # 狀態 3 = completed
                    from_status = AppointmentRepository._get_latest_status(conn, appt_id)
                    AppointmentRepository._insert_status_history(
                        conn, appt_id, from_status, 3, provider_user_id
                    )
                    
                    # 獲取 session_id 用於自動過號檢查
                    appointment = AppointmentRepository.get_appointment_by_id(appt_id)
                    if appointment:
                        session_id = appointment["session_id"]
                        AppointmentRepository._auto_mark_no_show(conn, session_id, provider_user_id)
                else:
                    # 檢查 provider_id 是否匹配
                    existing_provider_id = row["provider_id"]
                    enct_id = row["enct_id"]
                    
                    if existing_provider_id != provider_user_id:
                        # Provider 不匹配，檢查 appointment 的 session 是否屬於當前 provider
                        appointment = AppointmentRepository.get_appointment_by_id(appt_id)
                        if appointment:
                            session = SessionRepository.get_session_by_id(appointment["session_id"])
                            if session and session["provider_id"] == provider_user_id:
                                # Appointment 屬於當前 provider 的 session，但 encounter 由另一個 provider 創建
                                # 這可能是數據不一致的情況，允許當前 provider 更新並修正 provider_id
                                cur.execute(
                                    """
                                    UPDATE ENCOUNTER
                                    SET provider_id = %s,
                                        status = %s,
                                        chief_complaint = %s,
                                        subjective = %s,
                                        assessment = %s,
                                        plan = %s
                                    WHERE enct_id = %s
                                    RETURNING enct_id, appt_id, provider_id, encounter_at,
                                              status, chief_complaint, subjective, assessment, plan;
                                    """,
                                    (
                                        provider_user_id,
                                        status,
                                        chief_complaint,
                                        subjective,
                                        assessment,
                                        plan,
                                        enct_id,
                                    ),
                                )
                            else:
                                # Appointment 不屬於當前 provider 的 session
                                conn.rollback()
                                raise Exception(
                                    f"Encounter already exists for appointment {appt_id} "
                                    f"with provider {existing_provider_id}. "
                                    f"Cannot update with provider {provider_user_id}."
                                )
                        else:
                            # Appointment 不存在
                            conn.rollback()
                            raise Exception(
                                f"Appointment {appt_id} not found."
                            )
                    else:
                        # Provider 匹配，正常更新
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
                    
                    # 當更新現有 encounter 時，檢查並更新 appointment 狀態為 completed (3)
                    # 但不要更新已取消的 appointment (status 4)
                    current_appt_status = AppointmentRepository._get_latest_status(conn, appt_id)
                    if current_appt_status is not None and current_appt_status != 3 and current_appt_status != 4:
                        # 如果當前狀態不是 "completed" 且不是 "cancelled"，更新為 "completed"
                        AppointmentRepository._insert_status_history(
                            conn, appt_id, current_appt_status, 3, provider_user_id
                        )
                        
                        # 獲取 session_id 用於自動過號檢查
                        appointment = AppointmentRepository.get_appointment_by_id(appt_id)
                        if appointment:
                            session_id = appointment["session_id"]
                            AppointmentRepository._auto_mark_no_show(conn, session_id, provider_user_id)

                result = cur.fetchone()
                conn.commit()
                return result
        except Exception as e:
            conn.rollback()
            raise e
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

