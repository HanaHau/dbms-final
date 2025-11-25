# repositories/session_repo.py
from psycopg2.extras import RealDictCursor
from ..pg_base import get_pg_conn


class SessionRepository:
    """處理門診時段（CLINIC_SESSION）相關的資料庫操作"""

    @staticmethod
    def list_clinic_sessions_for_provider(provider_user_id, from_date=None, to_date=None, status=None):
        """
        列出某位醫師的門診時段，可用日期區間與門診狀態過濾。
        回傳每個 session 目前已掛號人數 booked_count。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
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
                        cs.start_time,
                        cs.end_time,
                        cs.capacity,
                        cs.status,
                        COUNT(a.appt_id) AS booked_count
                    FROM CLINIC_SESSION cs
                    LEFT JOIN APPOINTMENT a ON a.session_id = cs.session_id
                    WHERE {where_clause}
                    GROUP BY cs.session_id,
                             cs.provider_id,
                             cs.date,
                             cs.start_time,
                             cs.end_time,
                             cs.capacity,
                             cs.status
                    ORDER BY cs.date, cs.start_time;
                    """,
                    params,
                )
                return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def create_clinic_session(provider_user_id, date_, start_time_, end_time_, capacity):
        """
        醫師新增門診時段。
        status 預設為 1（例如：尚未開始）。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO CLINIC_SESSION (
                        provider_id, date, start_time, end_time, capacity, status
                    )
                    VALUES (%s, %s, %s, %s, %s, 1)
                    RETURNING session_id, provider_id, date, start_time, end_time, capacity, status;
                    """,
                    (provider_user_id, date_, start_time_, end_time_, capacity),
                )
                conn.commit()
                return cur.fetchone()
        finally:
            conn.close()

    @staticmethod
    def update_clinic_session(provider_user_id, session_id, date_, start_time_, end_time_, capacity, status):
        """
        醫師更新自己的門診時段（日期、時間、人數上限、狀態）。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    UPDATE CLINIC_SESSION
                    SET date       = %s,
                        start_time = %s,
                        end_time   = %s,
                        capacity   = %s,
                        status     = %s
                    WHERE session_id = %s
                      AND provider_id = %s
                    RETURNING session_id, provider_id, date, start_time, end_time, capacity, status;
                    """,
                    (date_, start_time_, end_time_, capacity, status, session_id, provider_user_id),
                )
                row = cur.fetchone()
                conn.commit()
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
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        cs.session_id,
                        cs.provider_id,
                        cs.date,
                        cs.start_time,
                        cs.end_time,
                        cs.capacity,
                        cs.status,
                        pr.dept_id,
                        u.name AS provider_name,
                        pr.license_no,
                        d.name AS department_name,
                        d.location AS department_location
                    FROM CLINIC_SESSION cs
                    JOIN PROVIDER pr ON cs.provider_id = pr.user_id
                    JOIN "USER" u ON pr.user_id = u.user_id
                    LEFT JOIN DEPARTMENT d ON pr.dept_id = d.dept_id
                    WHERE cs.session_id = %s;
                    """,
                    (session_id,),
                )
                return cur.fetchone()
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
                    SELECT COUNT(a.appt_id) AS booked_count
                    FROM CLINIC_SESSION cs
                    LEFT JOIN APPOINTMENT a ON a.session_id = cs.session_id
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
                        COUNT(a.appt_id) AS booked_count
                    FROM CLINIC_SESSION cs
                    LEFT JOIN APPOINTMENT a ON a.session_id = cs.session_id
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
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                conditions = []
                params = []

                if dept_id is not None:
                    conditions.append("pr.dept_id = %s")
                    params.append(dept_id)

                if provider_id is not None:
                    conditions.append("cs.provider_id = %s")
                    params.append(provider_id)

                if date_ is not None:
                    conditions.append("cs.date = %s")
                    params.append(date_)

                where_clause = " AND ".join(conditions) if conditions else "1=1"

                cur.execute(
                    f"""
                    SELECT
                        cs.session_id,
                        cs.provider_id,
                        cs.date,
                        cs.start_time,
                        cs.end_time,
                        cs.capacity,
                        cs.status,
                        pr.dept_id,
                        u.name AS provider_name,
                        pr.license_no,
                        d.name AS department_name,
                        d.location AS department_location,
                        COUNT(a.appt_id) AS booked_count
                    FROM CLINIC_SESSION cs
                    JOIN PROVIDER pr ON cs.provider_id = pr.user_id
                    JOIN "USER" u ON pr.user_id = u.user_id
                    LEFT JOIN DEPARTMENT d ON pr.dept_id = d.dept_id
                    LEFT JOIN APPOINTMENT a ON a.session_id = cs.session_id
                    WHERE {where_clause}
                    GROUP BY cs.session_id,
                             cs.provider_id,
                             cs.date,
                             cs.start_time,
                             cs.end_time,
                             cs.capacity,
                             cs.status,
                             pr.dept_id,
                             u.name,
                             pr.license_no,
                             d.name,
                             d.location
                    ORDER BY cs.date, cs.start_time;
                    """,
                    params,
                )
                return cur.fetchall()
        finally:
            conn.close()

