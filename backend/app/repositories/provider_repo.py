# repositories/provider_repo.py
from psycopg2.extras import RealDictCursor
import psycopg2
from ..pg_base import get_pg_conn


class ProviderRepository:
    """處理 Provider 相關的資料庫操作"""

    @staticmethod
    def create_provider_account(name, hash_pwd, license_no, dept_id):
        """
        建立一個新的醫師帳號：
        - 在 USER 新增一筆 type = 'provider'
        - 在 PROVIDER 新增一筆
        回傳：{ user_id, name, license_no, dept_id, active }
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # USER - 使用自動生成的 user_id
                cur.execute(
                    """
                    INSERT INTO "USER" (name, hash_pwd, type)
                    VALUES (%s, %s, 'provider')
                    RETURNING user_id;
                    """,
                    (name, hash_pwd),
                )
                user_row = cur.fetchone()
                new_user_id = user_row["user_id"]

                # PROVIDER
                cur.execute(
                    """
                    INSERT INTO PROVIDER (user_id, dept_id, license_no, active)
                    VALUES (%s, %s, %s, TRUE)
                    RETURNING user_id, dept_id, license_no, active;
                    """,
                    (new_user_id, dept_id, license_no),
                )
                provider_row = cur.fetchone()
                conn.commit()

                provider_row["name"] = name
                return provider_row
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
    def authenticate_provider_by_license(license_no, hash_pwd):
        """
        用 license_no + hash_pwd 驗證醫師身份。
        成功回傳 provider + user 資訊，失敗回傳 None。
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
                        pr.dept_id,
                        pr.license_no,
                        pr.active
                    FROM PROVIDER pr
                    JOIN "USER" u ON pr.user_id = u.user_id
                    WHERE pr.license_no = %s
                      AND u.hash_pwd = %s
                      AND u.type = 'provider'
                      AND pr.active = TRUE;
                    """,
                    (license_no, hash_pwd),
                )
                return cur.fetchone()
        finally:
            conn.close()

    @staticmethod
    def get_provider_profile(provider_user_id):
        """
        取得某位醫師的基本資料（姓名、科別）。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        pr.user_id,
                        u.name,
                        pr.license_no,
                        pr.active,
                        pr.dept_id,
                        d.name     AS department_name,
                        d.location AS department_location
                    FROM PROVIDER pr
                    JOIN "USER" u   ON pr.user_id = u.user_id
                    LEFT JOIN DEPARTMENT d ON pr.dept_id = d.dept_id
                    WHERE pr.user_id = %s;
                    """,
                    (provider_user_id,),
                )
                return cur.fetchone()
        finally:
            conn.close()

