# repositories/patient_repo.py
from psycopg2.extras import RealDictCursor
import psycopg2
from ..pg_base import get_pg_conn


class PatientRepository:
    """處理病患（PATIENT）相關的資料庫操作"""

    @staticmethod
    def create_patient_account(name, hash_pwd, national_id, birth_date, sex, phone):
        """
        建立一個新的病患帳號：
        - 在 USER 新增一筆 type = 'patient'
        - 在 PATIENT 新增一筆
        回傳：{ user_id, name, national_id, birth_date, sex, phone }
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 步驟 1: 在 USER 表中創建記錄（type = 'patient'）
                cur.execute(
                    """
                    INSERT INTO "USER" (name, hash_pwd, type)
                    VALUES (%s, %s, 'patient')
                    RETURNING user_id;
                    """,
                    (name, hash_pwd),
                )
                user_row = cur.fetchone()
                
                # 驗證 USER 記錄是否成功創建
                if not user_row:
                    raise Exception("Failed to create USER record: INSERT did not return user_id")
                
                # 獲取新創建的 user_id
                new_user_id = user_row.get("user_id") if hasattr(user_row, 'get') else user_row["user_id"]
                
                if not new_user_id:
                    raise Exception(f"Failed to get user_id from USER INSERT result: {user_row}")

                # 步驟 2: 在 PATIENT 表中創建記錄（使用剛創建的 user_id）
                cur.execute(
                    """
                    INSERT INTO patient (user_id, national_id, birth_date, sex, phone)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING user_id, national_id, birth_date, sex, phone;
                    """,
                    (new_user_id, national_id, birth_date, sex, phone),
                )
                patient_row = cur.fetchone()
                
                # 驗證 PATIENT 記錄是否成功創建
                if not patient_row:
                    raise Exception(f"Failed to create PATIENT record with user_id={new_user_id}")
                
                # 提交事務（確保 USER 和 PATIENT 記錄都成功創建）
                conn.commit()

                # 添加 name 到返回結果
                patient_row["name"] = name
                return patient_row
        except psycopg2.IntegrityError as e:
            # 重新拋出 IntegrityError，讓 service 層處理
            conn.rollback()
            raise e
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def authenticate_patient_by_national_id(national_id, hash_pwd):
        """
        用 national_id + hash_pwd 驗證病患身份。
        成功回傳 patient + user 資訊，失敗回傳 None。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        u.user_id,
                        u.name,
                        u.type,
                        pt.national_id,
                        pt.birth_date,
                        pt.sex,
                        pt.phone
                    FROM patient pt
                    JOIN "USER" u ON pt.user_id = u.user_id
                    WHERE pt.national_id = %s
                      AND u.hash_pwd = %s
                      AND u.type = 'patient';
                    """,
                    (national_id, hash_pwd),
                )
                return cur.fetchone()
        finally:
            conn.close()

    @staticmethod
    def get_patient_profile(patient_user_id):
        """
        取得某位病患的基本資料（姓名、身分證字號、生日、電話）。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        pt.user_id,
                        u.name,
                        pt.national_id,
                        pt.birth_date,
                        pt.sex,
                        pt.phone,
                        COALESCE(COUNT(n.id), 0) AS no_show_count,
                        pt.banned_until
                    FROM patient pt
                    JOIN "USER" u ON pt.user_id = u.user_id
                    LEFT JOIN no_show_event n ON n.patient_id = pt.user_id
                    WHERE pt.user_id = %s
                    GROUP BY pt.user_id, u.name, pt.national_id, pt.birth_date, pt.sex, pt.phone, pt.banned_until;
                    """,
                    (patient_user_id,),
                )
                return cur.fetchone()
        finally:
            conn.close()

    @staticmethod
    def is_patient_banned(patient_id):
        """
        檢查病人是否被禁止掛號（達到三次爽約且在兩週內）。
        從 no_show_event 表計算爽約次數。
        回傳 (is_banned, banned_until) 元組。
        """
        from datetime import date, timedelta
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 從 no_show_event 表計算爽約次數
                cur.execute(
                    """
                    SELECT 
                        COUNT(*) AS no_show_count,
                        p.banned_until
                    FROM patient p
                    LEFT JOIN no_show_event n ON n.patient_id = p.user_id
                    WHERE p.user_id = %s
                    GROUP BY p.user_id, p.banned_until;
                    """,
                    (patient_id,),
                )
                row = cur.fetchone()
                if row is None:
                    return False, None
                
                no_show_count = row["no_show_count"] or 0
                banned_until = row["banned_until"]
                
                # 如果未達到三次爽約，直接返回
                if no_show_count < 3:
                    return False, None
                
                # 如果 banned_until 為空，設置為兩週後
                if banned_until is None:
                    banned_until = date.today() + timedelta(days=14)
                    cur.execute(
                        """
                        UPDATE patient
                        SET banned_until = %s
                        WHERE user_id = %s;
                        """,
                        (banned_until, patient_id),
                    )
                    conn.commit()
                    return True, banned_until
                
                # 檢查是否還在禁止期內
                if date.today() <= banned_until:
                    return True, banned_until
                
                # 禁止期已過，清除禁止日期（但保留 no_show_event 記錄）
                cur.execute(
                    """
                    UPDATE patient
                    SET banned_until = NULL
                    WHERE user_id = %s;
                    """,
                    (patient_id,),
                )
                conn.commit()
                return False, None
        finally:
            conn.close()

    @staticmethod
    def increment_no_show_count(patient_id, appt_id):
        """
        累計病人的爽約次數。
        在 no_show_event 表中插入一筆記錄，並檢查是否需要設置 banned_until。
        """
        from datetime import date, timedelta, datetime
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 檢查是否已經存在記錄，避免重複插入
                cur.execute(
                    """
                    SELECT 1 FROM no_show_event
                    WHERE patient_id = %s AND appt_id = %s;
                    """,
                    (patient_id, appt_id),
                )
                if cur.fetchone():
                    # 記錄已存在，不需要重複插入
                    return
                
                # 插入 no_show_event 記錄
                cur.execute(
                    """
                    INSERT INTO no_show_event (patient_id, appt_id, recorded_at)
                    VALUES (%s, %s, %s);
                    """,
                    (patient_id, appt_id, datetime.now()),
                )
                
                # 計算新的爽約次數
                cur.execute(
                    """
                    SELECT COUNT(*) AS no_show_count
                    FROM no_show_event
                    WHERE patient_id = %s;
                    """,
                    (patient_id,),
                )
                row = cur.fetchone()
                new_count = row["no_show_count"] if row else 0
                
                # 如果達到 3 次或以上，設置 banned_until
                if new_count >= 3:
                    banned_until = date.today() + timedelta(days=14)
                    cur.execute(
                        """
                        UPDATE patient
                        SET banned_until = %s
                        WHERE user_id = %s
                          AND (banned_until IS NULL OR banned_until < %s);
                        """,
                        (banned_until, patient_id, banned_until),
                    )
                
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
