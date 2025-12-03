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
                    INSERT INTO PATIENT (user_id, national_id, birth_date, sex, phone)
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
                    FROM PATIENT pt
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
                        COALESCE(pt.no_show_count, 0) AS no_show_count,
                        pt.banned_until
                    FROM PATIENT pt
                    JOIN "USER" u ON pt.user_id = u.user_id
                    WHERE pt.user_id = %s;
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
        回傳 (is_banned, banned_until) 元組。
        """
        from datetime import date, timedelta
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT no_show_count, banned_until
                    FROM PATIENT
                    WHERE user_id = %s;
                    """,
                    (patient_id,),
                )
                row = cur.fetchone()
                if row is None:
                    return False, None
                
                no_show_count = row["no_show_count"] or 0
                banned_until = row["banned_until"]
                
                # 如果達到三次爽約
                if no_show_count >= 3:
                    # 如果 banned_until 為空，設置為兩週後
                    if banned_until is None:
                        banned_until = date.today() + timedelta(days=14)
                        cur.execute(
                            """
                            UPDATE PATIENT
                            SET banned_until = %s
                            WHERE user_id = %s;
                            """,
                            (banned_until, patient_id),
                        )
                        conn.commit()
                    
                    # 檢查是否還在禁止期內
                    if date.today() <= banned_until:
                        return True, banned_until
                    else:
                        # 禁止期已過，重置爽約次數和禁止日期
                        cur.execute(
                            """
                            UPDATE PATIENT
                            SET no_show_count = 0, banned_until = NULL
                            WHERE user_id = %s;
                            """,
                            (patient_id,),
                        )
                        conn.commit()
                        return False, None
                
                return False, None
        finally:
            conn.close()

    @staticmethod
    def increment_no_show_count(patient_id):
        """
        累計病人的爽約次數。
        """
        from datetime import date, timedelta
        conn = get_pg_conn()
        try:
            conn.autocommit = False
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 獲取當前爽約次數
                cur.execute(
                    """
                    SELECT COALESCE(no_show_count, 0) AS no_show_count
                    FROM PATIENT
                    WHERE user_id = %s;
                    """,
                    (patient_id,),
                )
                row = cur.fetchone()
                if row is None:
                    conn.rollback()
                    return
                
                new_count = (row["no_show_count"] or 0) + 1
                
                # 更新爽約次數
                # 如果達到三次，設置禁止日期為兩週後
                if new_count >= 3:
                    banned_until = date.today() + timedelta(days=14)
                    cur.execute(
                        """
                        UPDATE PATIENT
                        SET no_show_count = %s, banned_until = %s
                        WHERE user_id = %s;
                        """,
                        (new_count, banned_until, patient_id),
                    )
                else:
                    cur.execute(
                        """
                        UPDATE PATIENT
                        SET no_show_count = %s
                        WHERE user_id = %s;
                        """,
                        (new_count, patient_id),
                    )
                
                conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
