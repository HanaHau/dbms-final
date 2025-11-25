# repositories/patient_repo.py
from psycopg2.extras import RealDictCursor
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
                # USER - 使用自動生成的 user_id
                cur.execute(
                    """
                    INSERT INTO "USER" (name, hash_pwd, type)
                    VALUES (%s, %s, 'patient')
                    RETURNING user_id;
                    """,
                    (name, hash_pwd),
                )
                user_row = cur.fetchone()
                new_user_id = user_row["user_id"]

                # PATIENT
                cur.execute(
                    """
                    INSERT INTO PATIENT (user_id, national_id, birth_date, sex, phone)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING user_id, national_id, birth_date, sex, phone;
                    """,
                    (new_user_id, national_id, birth_date, sex, phone),
                )
                patient_row = cur.fetchone()
                conn.commit()

                patient_row["name"] = name
                return patient_row
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
                        pt.phone
                    FROM PATIENT pt
                    JOIN "USER" u ON pt.user_id = u.user_id
                    WHERE pt.user_id = %s;
                    """,
                    (patient_user_id,),
                )
                return cur.fetchone()
        finally:
            conn.close()
