# repositories/appointment_repo.py
from psycopg2.extras import RealDictCursor
from ..pg_base import get_pg_conn


class AppointmentRepository:
    """處理掛號（APPOINTMENT）相關的資料庫操作"""

    @staticmethod
    def _get_latest_status(conn, appt_id):
        """取得掛號的最新狀態（內部輔助方法）"""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT to_status
                FROM APPOINTMENT_STATUS_HISTORY
                WHERE appt_id = %s
                ORDER BY changed_at DESC
                LIMIT 1;
                """,
                (appt_id,),
            )
            row = cur.fetchone()
            return row["to_status"] if row is not None else None

    @staticmethod
    def _insert_status_history(conn, appt_id, from_status, to_status, changed_by):
        """插入狀態歷史記錄（內部輔助方法）"""
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO APPOINTMENT_STATUS_HISTORY (
                    appt_id, from_status, to_status, changed_by, changed_at
                )
                VALUES (%s, %s, %s, %s, NOW());
                """,
                (appt_id, from_status, to_status, changed_by),
            )

    @staticmethod
    def get_appointment_by_id(appt_id):
        """
        根據 appt_id 取得掛號資訊，包含 patient_id。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        a.appt_id,
                        a.slot_seq,
                        a.patient_id,
                        a.session_id
                    FROM APPOINTMENT a
                    WHERE a.appt_id = %s;
                    """,
                    (appt_id,),
                )
                return cur.fetchone()
        finally:
            conn.close()

    @staticmethod
    def list_appointments_for_session(provider_user_id, session_id):
        """
        列出某個門診時段的掛號清單（只允許看自己的 session）。
        包含：病人姓名、slot_seq、目前掛號狀態。
        狀態來自 APPOINTMENT_STATUS_HISTORY 最新一筆 to_status。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        a.appt_id,
                        a.slot_seq,
                        a.patient_id,
                        u_pt.name AS patient_name,
                        ash_latest.to_status AS status,
                        ash_latest.changed_at AS status_changed_at
                    FROM CLINIC_SESSION cs
                    JOIN APPOINTMENT a ON a.session_id = cs.session_id
                    JOIN PATIENT p ON a.patient_id = p.user_id
                    JOIN "USER" u_pt ON p.user_id = u_pt.user_id
                    LEFT JOIN LATERAL (
                        SELECT ash.to_status, ash.changed_at
                        FROM APPOINTMENT_STATUS_HISTORY ash
                        WHERE ash.appt_id = a.appt_id
                        ORDER BY ash.changed_at DESC
                        LIMIT 1
                    ) AS ash_latest ON TRUE
                    WHERE cs.session_id = %s
                      AND cs.provider_id = %s
                    ORDER BY a.slot_seq;
                    """,
                    (session_id, provider_user_id),
                )
                return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def update_appointment_status(provider_user_id, appt_id, new_status):
        """
        醫師更新掛號狀態：
        - 查目前最新狀態作為 from_status
        - 寫一筆新的 APPOINTMENT_STATUS_HISTORY
        """
        conn = get_pg_conn()
        try:
            from_status = AppointmentRepository._get_latest_status(conn, appt_id)
            AppointmentRepository._insert_status_history(
                conn, appt_id, from_status, new_status, provider_user_id
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def list_appointments_for_patient(patient_id):
        """
        列出某位病人的所有掛號。
        包含：掛號 ID、門診時段資訊、slot_seq、目前掛號狀態。
        狀態來自 APPOINTMENT_STATUS_HISTORY 最新一筆 to_status。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        a.appt_id,
                        a.slot_seq,
                        a.patient_id,
                        a.session_id,
                        cs.date AS session_date,
                        cs.start_time AS session_start_time,
                        cs.end_time AS session_end_time,
                        cs.provider_id,
                        u_provider.name AS provider_name,
                        pr.dept_id,
                        COALESCE(d.name, '') AS dept_name,
                        COALESCE(ash_latest.to_status, 1) AS status,
                        ash_latest.changed_at AS status_changed_at
                    FROM APPOINTMENT a
                    JOIN CLINIC_SESSION cs ON a.session_id = cs.session_id
                    JOIN PROVIDER pr ON cs.provider_id = pr.user_id
                    JOIN "USER" u_provider ON pr.user_id = u_provider.user_id
                    LEFT JOIN DEPARTMENT d ON pr.dept_id = d.dept_id
                    LEFT JOIN LATERAL (
                        SELECT ash.to_status, ash.changed_at
                        FROM APPOINTMENT_STATUS_HISTORY ash
                        WHERE ash.appt_id = a.appt_id
                        ORDER BY ash.changed_at DESC
                        LIMIT 1
                    ) AS ash_latest ON TRUE
                    WHERE a.patient_id = %s
                    ORDER BY cs.date DESC, cs.start_time DESC;
                    """,
                    (patient_id,),
                )
                return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def update_appointment_status_by_patient(patient_id, appt_id, new_status):
        """
        病人更新掛號狀態（例如：報到 checkin）：
        - 驗證 patient_id 是否匹配
        - 查目前最新狀態作為 from_status
        - 寫一筆新的 APPOINTMENT_STATUS_HISTORY
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 驗證 appt_id 和 patient_id 是否匹配
                cur.execute(
                    """
                    SELECT appt_id, patient_id
                    FROM APPOINTMENT
                    WHERE appt_id = %s AND patient_id = %s;
                    """,
                    (appt_id, patient_id),
                )
                row = cur.fetchone()
                if row is None:
                    return None

            # 使用統一的狀態更新邏輯
            from_status = AppointmentRepository._get_latest_status(conn, appt_id)
            AppointmentRepository._insert_status_history(
                conn, appt_id, from_status, new_status, patient_id
            )

            conn.commit()
            return {"appt_id": appt_id, "status_updated": True}
        finally:
            conn.close()

    @staticmethod
    def create_appointment(patient_id, session_id):
        """
        建立掛號：
        - 檢查是否已在該 session 重複掛號
        - 檢查 session 容量是否已滿
        - 使用 transaction + FOR UPDATE 避免併行衝突
        - slot_seq = 已掛號人數 + 1
        - 寫入 APPOINTMENT_STATUS_HISTORY（初始狀態）
        """
        conn = get_pg_conn()
        try:
            # 確保使用事務
            conn.autocommit = False
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 檢查是否已在該 session 重複掛號
                cur.execute(
                    """
                    SELECT appt_id
                    FROM APPOINTMENT
                    WHERE patient_id = %s AND session_id = %s;
                    """,
                    (patient_id, session_id),
                )
                if cur.fetchone() is not None:
                    conn.rollback()
                    raise Exception("Patient already has an appointment for this session")

                # 檢查 session 容量並鎖定 session 記錄，避免併行衝突
                cur.execute(
                    """
                    SELECT capacity, provider_id, date, end_time, status
                    FROM CLINIC_SESSION
                    WHERE session_id = %s
                    FOR UPDATE;
                    """,
                    (session_id,),
                )
                session_row = cur.fetchone()
                if session_row is None:
                    conn.rollback()
                    raise Exception("Session not found")

                capacity = session_row["capacity"]
                provider_id = session_row["provider_id"]
                session_date = session_row["date"]
                session_end_time = session_row["end_time"]
                session_status = session_row["status"]

                # 檢查 session 狀態
                if session_status == 0:
                    conn.rollback()
                    raise Exception("Session is cancelled")

                # 檢查是否已過門診時間，如果已過則自動更新 status 為 0（停診）
                from datetime import datetime, date, time
                now = datetime.now()
                session_datetime = datetime.combine(session_date, session_end_time)
                if now > session_datetime:
                    # 自動將 status 更新為 0（停診）
                    cur.execute(
                        """
                        UPDATE CLINIC_SESSION
                        SET status = 0
                        WHERE session_id = %s;
                        """,
                        (session_id,),
                    )
                    conn.rollback()
                    raise Exception("Session has ended, cannot book appointment")

                # 計算已預約人數（在鎖定 session 後）
                cur.execute(
                    """
                    SELECT COUNT(*) AS booked_count
                    FROM APPOINTMENT
                    WHERE session_id = %s;
                    """,
                    (session_id,),
                )
                row = cur.fetchone()
                booked_count = row["booked_count"] if row else 0

                if booked_count >= capacity:
                    conn.rollback()
                    raise Exception("Session is full")

                slot_seq = booked_count + 1

                # 插入 APPOINTMENT - 使用自動生成的 appt_id
                cur.execute(
                    """
                    INSERT INTO APPOINTMENT (patient_id, session_id, slot_seq)
                    VALUES (%s, %s, %s)
                    RETURNING appt_id, patient_id, session_id, slot_seq;
                    """,
                    (patient_id, session_id, slot_seq),
                )
                appt = cur.fetchone()
                new_appt_id = appt["appt_id"]

                # 寫入 APPOINTMENT_STATUS_HISTORY（初始狀態，假設狀態 1 為「已預約」）
                # 注意：changed_by 必須是 provider_id，因為外鍵約束指向 provider 表
                # 雖然是病人建立的，但系統層面記錄為 provider（因為外鍵約束限制）
                cur.execute(
                    """
                    INSERT INTO APPOINTMENT_STATUS_HISTORY (
                        appt_id, from_status, to_status, changed_by, changed_at
                    )
                    VALUES (%s, NULL, 1, %s, NOW());
                    """,
                    (new_appt_id, provider_id),
                )

                conn.commit()
                return appt
        except Exception as e:
            import traceback
            print(f"❌ AppointmentRepository.create_appointment 錯誤:")
            print(f"   patient_id: {patient_id}, session_id: {session_id}")
            print(f"   錯誤訊息: {str(e)}")
            print(f"   錯誤堆疊:\n{traceback.format_exc()}")
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def cancel_appointment(appt_id, patient_id):
        """
        取消掛號：
        - 驗證 patient_id 是否匹配
        - 更新狀態為「已取消」（假設狀態 0 為「已取消」）
        - 寫入 APPOINTMENT_STATUS_HISTORY
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 驗證 appt_id 和 patient_id 是否匹配
                cur.execute(
                    """
                    SELECT appt_id, patient_id
                    FROM APPOINTMENT
                    WHERE appt_id = %s AND patient_id = %s;
                    """,
                    (appt_id, patient_id),
                )
                row = cur.fetchone()
                if row is None:
                    return None

                # 使用統一的狀態更新邏輯
                from_status = AppointmentRepository._get_latest_status(conn, appt_id)
                AppointmentRepository._insert_status_history(
                    conn, appt_id, from_status, 0, patient_id
                )

                conn.commit()
                return {"appt_id": appt_id, "cancelled": True}
        finally:
            conn.close()

    @staticmethod
    def modify_appointment(appt_id, old_session_id, new_session_id):
        """
        修改掛號（更換門診時段）：
        - 使用固定鎖序（按照 session_id 大小順序）避免死鎖
        - 更新 session_id 和 slot_seq
        - 寫入 APPOINTMENT_STATUS_HISTORY
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 固定鎖序：按照 session_id 大小順序鎖定，避免死鎖
                first_session_id = min(old_session_id, new_session_id)
                second_session_id = max(old_session_id, new_session_id)

                # 先鎖定較小的 session_id
                cur.execute(
                    """
                    SELECT COUNT(*) AS booked_count
                    FROM APPOINTMENT
                    WHERE session_id = %s
                    FOR UPDATE;
                    """,
                    (first_session_id,),
                )

                # 再鎖定較大的 session_id（如果不同）
                if first_session_id != second_session_id:
                    cur.execute(
                        """
                        SELECT COUNT(*) AS booked_count
                        FROM APPOINTMENT
                        WHERE session_id = %s
                        FOR UPDATE;
                        """,
                        (second_session_id,),
                    )

                # 驗證 appt_id 是否存在且屬於 old_session_id
                cur.execute(
                    """
                    SELECT appt_id, patient_id, session_id, slot_seq
                    FROM APPOINTMENT
                    WHERE appt_id = %s AND session_id = %s;
                    """,
                    (appt_id, old_session_id),
                )
                appt_row = cur.fetchone()
                if appt_row is None:
                    conn.rollback()
                    return None

                # 計算新 session 的 slot_seq
                cur.execute(
                    """
                    SELECT COUNT(*) AS booked_count
                    FROM APPOINTMENT
                    WHERE session_id = %s;
                    """,
                    (new_session_id,),
                )
                new_count_row = cur.fetchone()
                new_booked_count = new_count_row["booked_count"] if new_count_row else 0
                new_slot_seq = new_booked_count + 1

                # 更新 APPOINTMENT
                cur.execute(
                    """
                    UPDATE APPOINTMENT
                    SET session_id = %s, slot_seq = %s
                    WHERE appt_id = %s
                    RETURNING appt_id, patient_id, session_id, slot_seq;
                    """,
                    (new_session_id, new_slot_seq, appt_id),
                )
                updated_appt = cur.fetchone()

                # 使用統一的狀態更新邏輯
                from_status = AppointmentRepository._get_latest_status(conn, appt_id)
                AppointmentRepository._insert_status_history(
                    conn, appt_id, from_status, 2, appt_row["patient_id"]
                )

                conn.commit()
                return updated_appt
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

