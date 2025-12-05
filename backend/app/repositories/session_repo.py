# repositories/session_repo.py
from psycopg2.extras import RealDictCursor
from ..pg_base import get_pg_conn
from ..lib.period_utils import period_to_start_time, period_to_end_time, is_period_time_valid


class SessionRepository:
    """處理門診時段（CLINIC_SESSION）相關的資料庫操作"""

    @staticmethod
    def list_clinic_sessions_for_provider(provider_user_id, from_date=None, to_date=None, status=None):
        """
        列出某位醫師的門診時段，可用日期區間與門診狀態過濾。
        回傳每個 session 目前已掛號人數 booked_count。
        自動將已過期的 session status 更新為 0（停診）。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 先自動更新已過期的 session status（使用 period 計算結束時間）
                cur.execute(
                    """
                    UPDATE CLINIC_SESSION
                    SET status = 0
                    WHERE provider_id = %s
                      AND status = 1
                      AND (
                          date < CURRENT_DATE 
                          OR (
                              date = CURRENT_DATE 
                              AND (
                                  (period = 1 AND CURRENT_TIME >= TIME '12:00:00')
                                  OR (period = 2 AND CURRENT_TIME >= TIME '17:00:00')
                                  OR (period = 3 AND CURRENT_TIME >= TIME '21:00:00')
                              )
                          )
                      );
                    """,
                    (provider_user_id,)
                )
                conn.commit()

                params = [provider_user_id]
                conditions = ["cs.provider_id = %s"]

                if from_date is not None:
                    conditions.append("cs.date >= %s")
                    params.append(from_date)
                if to_date is not None:
                    conditions.append("cs.date <= %s")
                    params.append(to_date)
                if status is not None:
                    conditions.append("cs.status = %s")
                    params.append(status)

                where_clause = " AND ".join(conditions)

                cur.execute(
                    f"""
                    SELECT
                        cs.session_id,
                        cs.provider_id,
                        cs.date,
                        cs.period,
                        cs.capacity,
                        cs.status,
                        COUNT(CASE WHEN COALESCE(ash_latest.to_status, 1) != 0 THEN a.appt_id END) AS booked_count
                    FROM CLINIC_SESSION cs
                    LEFT JOIN APPOINTMENT a ON a.session_id = cs.session_id
                    LEFT JOIN LATERAL (
                        SELECT ash.to_status
                        FROM APPOINTMENT_STATUS_HISTORY ash
                        WHERE ash.appt_id = a.appt_id
                        ORDER BY ash.changed_at DESC
                        LIMIT 1
                    ) AS ash_latest ON TRUE
                    WHERE {where_clause}
                    GROUP BY cs.session_id,
                             cs.provider_id,
                             cs.date,
                             cs.period,
                             cs.capacity,
                             cs.status
                    ORDER BY cs.date, cs.period;
                    """,
                    params,
                )
                rows = cur.fetchall()
                # 為每個 session 添加計算的 start_time 和 end_time（用於向後兼容）
                for row in rows:
                    row["start_time"] = period_to_start_time(row["period"])
                    row["end_time"] = period_to_end_time(row["period"])
                return rows
        finally:
            conn.close()

    @staticmethod
    def create_clinic_session(provider_user_id, date_, period, capacity):
        """
        醫師新增門診時段。
        status 預設為 1（開診）。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO CLINIC_SESSION (
                        provider_id, date, period, capacity, status
                    )
                    VALUES (%s, %s, %s, %s, 1)
                    RETURNING session_id, provider_id, date, period, capacity, status;
                    """,
                    (provider_user_id, date_, period, capacity),
                )
                row = cur.fetchone()
                conn.commit()
                # 添加計算的 start_time 和 end_time（用於向後兼容）
                if row:
                    row["start_time"] = period_to_start_time(row["period"])
                    row["end_time"] = period_to_end_time(row["period"])
                return row
        finally:
            conn.close()

    @staticmethod
    def update_clinic_session(provider_user_id, session_id, date_, period, capacity, status):
        """
        醫師更新自己的門診時段（日期、時段、人數上限、狀態）。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    UPDATE CLINIC_SESSION
                    SET date       = %s,
                        period     = %s,
                        capacity   = %s,
                        status     = %s
                    WHERE session_id = %s
                      AND provider_id = %s
                    RETURNING session_id, provider_id, date, period, capacity, status;
                    """,
                    (date_, period, capacity, status, session_id, provider_user_id),
                )
                row = cur.fetchone()
                conn.commit()
                # 添加計算的 start_time 和 end_time（用於向後兼容）
                if row:
                    row["start_time"] = period_to_start_time(row["period"])
                    row["end_time"] = period_to_end_time(row["period"])
                return row
        finally:
            conn.close()

    @staticmethod
    def cancel_clinic_session(provider_user_id, session_id, cancel_status=0):
        """
        醫師取消門診時段（把 status 更新為 cancel_status，例如 0 = 停診）。
        回傳 True/False 表示有沒有更新到。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE CLINIC_SESSION
                    SET status = %s
                    WHERE session_id = %s
                      AND provider_id = %s;
                    """,
                    (cancel_status, session_id, provider_user_id),
                )
                conn.commit()
                return cur.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def get_session_by_id(session_id):
        """
        根據 session_id 取得門診時段資訊，包含 provider 和 department 資訊。
        自動將已過期的 session status 更新為 0（停診）。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 先自動更新已過期的 session status（使用 period 計算結束時間）
                cur.execute(
                    """
                    UPDATE CLINIC_SESSION
                    SET status = 0
                    WHERE session_id = %s
                      AND status = 1
                      AND (
                          date < CURRENT_DATE 
                          OR (
                              date = CURRENT_DATE 
                              AND (
                                  (period = 1 AND CURRENT_TIME >= TIME '12:00:00')
                                  OR (period = 2 AND CURRENT_TIME >= TIME '17:00:00')
                                  OR (period = 3 AND CURRENT_TIME >= TIME '21:00:00')
                              )
                          )
                      );
                    """,
                    (session_id,)
                )
                conn.commit()

                cur.execute(
                    """
                    SELECT
                        cs.session_id,
                        cs.provider_id,
                        cs.date,
                        cs.period,
                        cs.capacity,
                        cs.status,
                        pr.dept_id,
                        u.name AS provider_name,
                        pr.license_no,
                        d.name AS dept_name,
                        d.location AS department_location
                    FROM CLINIC_SESSION cs
                    JOIN PROVIDER pr ON cs.provider_id = pr.user_id
                    JOIN "USER" u ON pr.user_id = u.user_id
                    LEFT JOIN DEPARTMENT d ON pr.dept_id = d.dept_id
                    WHERE cs.session_id = %s;
                    """,
                    (session_id,),
                )
                row = cur.fetchone()
                # 添加計算的 start_time 和 end_time（用於向後兼容）
                if row:
                    row["start_time"] = period_to_start_time(row["period"])
                    row["end_time"] = period_to_end_time(row["period"])
                return row
        finally:
            conn.close()

    @staticmethod
    def get_booked_count(session_id):
        """
        取得某個門診時段的已預約數量。
        如果 session 不存在，回傳 None。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor() as cur:
                # 先檢查 session 是否存在
                cur.execute(
                    "SELECT session_id FROM CLINIC_SESSION WHERE session_id = %s;",
                    (session_id,),
                )
                if not cur.fetchone():
                    return None

                cur.execute(
                    """
                    SELECT COUNT(CASE WHEN COALESCE(ash_latest.to_status, 1) != 0 THEN a.appt_id END) AS booked_count
                    FROM CLINIC_SESSION cs
                    LEFT JOIN APPOINTMENT a ON a.session_id = cs.session_id
                    LEFT JOIN LATERAL (
                        SELECT ash.to_status
                        FROM APPOINTMENT_STATUS_HISTORY ash
                        WHERE ash.appt_id = a.appt_id
                        ORDER BY ash.changed_at DESC
                        LIMIT 1
                    ) AS ash_latest ON TRUE
                    WHERE cs.session_id = %s
                    GROUP BY cs.session_id;
                    """,
                    (session_id,),
                )
                row = cur.fetchone()
                return row[0] if row else 0
        finally:
            conn.close()

    @staticmethod
    def is_session_time_valid(session_date, period):
        """
        檢查門診時段是否在時間範圍內（當前時間在該 period 的時間範圍內）。
        回傳 (is_valid, session_info) 元組。
        """
        conn = get_pg_conn()
        try:
            is_valid = is_period_time_valid(session_date, period)
            # 返回 session_info（包含計算的時間）
            session_info = {
                "date": session_date,
                "period": period,
                "start_time": period_to_start_time(period),
                "end_time": period_to_end_time(period),
            }
            return is_valid, session_info
        finally:
            conn.close()

    @staticmethod
    def get_remaining_capacity(session_id):
        """
        取得某個門診時段的剩餘容量。
        回傳：capacity - booked_count
        """
        conn = get_pg_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        cs.capacity,
                        COUNT(CASE WHEN COALESCE(ash_latest.to_status, 1) != 0 THEN a.appt_id END) AS booked_count
                    FROM CLINIC_SESSION cs
                    LEFT JOIN APPOINTMENT a ON a.session_id = cs.session_id
                    LEFT JOIN LATERAL (
                        SELECT ash.to_status
                        FROM APPOINTMENT_STATUS_HISTORY ash
                        WHERE ash.appt_id = a.appt_id
                        ORDER BY ash.changed_at DESC
                        LIMIT 1
                    ) AS ash_latest ON TRUE
                    WHERE cs.session_id = %s
                    GROUP BY cs.session_id, cs.capacity;
                    """,
                    (session_id,),
                )
                row = cur.fetchone()
                if row:
                    capacity = row[0]
                    booked_count = row[1] if row[1] else 0
                    return max(0, capacity - booked_count)
                return None
        finally:
            conn.close()

    @staticmethod
    def search_sessions(dept_id=None, provider_id=None, date_=None):
        """
        搜尋門診時段，可根據科別、醫師、日期過濾。
        回傳每個 session 的資訊，包含 provider 和 department 資訊，以及已預約人數。
        自動將已過期的 session status 更新為 0（停診）。
        
        注意：門診的科別（dept_name）來自該門診醫師的科別。
        查詢邏輯：CLINIC_SESSION → PROVIDER (provider_id) → DEPARTMENT (dept_id)
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 先自動更新已過期的 session status（使用 period 計算結束時間）
                cur.execute(
                    """
                    UPDATE CLINIC_SESSION
                    SET status = 0
                    WHERE status = 1
                      AND (
                          date < CURRENT_DATE 
                          OR (
                              date = CURRENT_DATE 
                              AND (
                                  (period = 1 AND CURRENT_TIME >= TIME '12:00:00')
                                  OR (period = 2 AND CURRENT_TIME >= TIME '17:00:00')
                                  OR (period = 3 AND CURRENT_TIME >= TIME '21:00:00')
                              )
                          )
                      );
                    """
                )
                conn.commit()

                conditions = []
                params = []

                # 只顯示正常狀態的門診（status = 1），不顯示已停診的門診
                conditions.append("cs.status = 1")

                if dept_id is not None:
                    conditions.append("pr.dept_id = %s")
                    params.append(dept_id)

                if provider_id is not None:
                    conditions.append("cs.provider_id = %s")
                    params.append(provider_id)

                if date_ is not None:
                    conditions.append("cs.date = %s")
                    params.append(date_)

                where_clause = " AND ".join(conditions)

                cur.execute(
                    f"""
                    SELECT
                        cs.session_id,
                        cs.provider_id,
                        cs.date,
                        cs.period,
                        cs.capacity,
                        cs.status,
                        pr.dept_id,
                        u.name AS provider_name,
                        pr.license_no,
                        d.name AS dept_name,
                        d.location AS department_location,
                        COUNT(CASE WHEN COALESCE(ash_latest.to_status, 1) != 0 THEN a.appt_id END) AS booked_count
                    FROM CLINIC_SESSION cs
                    JOIN PROVIDER pr ON cs.provider_id = pr.user_id
                    JOIN "USER" u ON pr.user_id = u.user_id
                    LEFT JOIN DEPARTMENT d ON pr.dept_id = d.dept_id
                    LEFT JOIN APPOINTMENT a ON a.session_id = cs.session_id
                    LEFT JOIN LATERAL (
                        SELECT ash.to_status
                        FROM APPOINTMENT_STATUS_HISTORY ash
                        WHERE ash.appt_id = a.appt_id
                        ORDER BY ash.changed_at DESC
                        LIMIT 1
                    ) AS ash_latest ON TRUE
                    WHERE {where_clause}
                    GROUP BY cs.session_id,
                             cs.provider_id,
                             cs.date,
                             cs.period,
                             cs.capacity,
                             cs.status,
                             pr.dept_id,
                             u.name,
                             pr.license_no,
                             d.name,
                             d.location
                    ORDER BY cs.date, cs.period;
                    """,
                    params,
                )
                rows = cur.fetchall()
                # 為每個 session 添加計算的 start_time 和 end_time（用於向後兼容）
                for row in rows:
                    row["start_time"] = period_to_start_time(row["period"])
                    row["end_time"] = period_to_end_time(row["period"])
                return rows
        finally:
            conn.close()

    @staticmethod
    def update_expired_sessions(provider_id=None):
        """
        更新所有已過期的門診時段狀態為停診（status = 0）。
        如果提供 provider_id，只更新該醫師的門診時段。
        回傳更新的數量。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor() as cur:
                if provider_id is not None:
                    cur.execute(
                        """
                        UPDATE CLINIC_SESSION
                        SET status = 0
                        WHERE provider_id = %s
                          AND status = 1
                          AND (
                              date < CURRENT_DATE 
                              OR (
                                  date = CURRENT_DATE 
                                  AND (
                                      (period = 1 AND CURRENT_TIME >= TIME '12:00:00')
                                      OR (period = 2 AND CURRENT_TIME >= TIME '17:00:00')
                                      OR (period = 3 AND CURRENT_TIME >= TIME '21:00:00')
                                  )
                              )
                          );
                        """,
                        (provider_id,)
                    )
                else:
                    cur.execute(
                        """
                        UPDATE CLINIC_SESSION
                        SET status = 0
                        WHERE status = 1
                          AND (
                              date < CURRENT_DATE 
                              OR (
                                  date = CURRENT_DATE 
                                  AND (
                                      (period = 1 AND CURRENT_TIME >= TIME '12:00:00')
                                      OR (period = 2 AND CURRENT_TIME >= TIME '17:00:00')
                                      OR (period = 3 AND CURRENT_TIME >= TIME '21:00:00')
                                  )
                              )
                          );
                        """
                    )
                updated_count = cur.rowcount
                conn.commit()
                return updated_count
        finally:
            conn.close()

