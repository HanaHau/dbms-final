# repositories/diagnosis_repo.py
from psycopg2.extras import RealDictCursor
from ..pg_base import get_pg_conn


class DiagnosisRepository:
    """處理診斷（DIAGNOSIS）相關的資料庫操作"""
    
    # 緩存 DISEASE 表的描述欄位名稱
    _disease_desc_field = None
    
    @staticmethod
    def _get_disease_desc_field(conn):
        """獲取 DISEASE 表的描述欄位名稱（緩存結果）"""
        if DiagnosisRepository._disease_desc_field is not None:
            return DiagnosisRepository._disease_desc_field
        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'disease' 
                AND column_name IN ('description', 'name', 'disease_name')
                LIMIT 1;
            """)
            row = cur.fetchone()
            if row:
                DiagnosisRepository._disease_desc_field = row[0]
            else:
                # 如果沒有描述欄位，使用 code_icd
                DiagnosisRepository._disease_desc_field = 'code_icd'
        
        return DiagnosisRepository._disease_desc_field

    @staticmethod
    def list_diagnoses_for_encounter(enct_id):
        """
        查詢一個就診紀錄的所有診斷。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                desc_field = DiagnosisRepository._get_disease_desc_field(conn)
                
                cur.execute(
                    f"""
                    SELECT
                        d.enct_id,
                        d.code_icd,
                        dis.{desc_field} AS description,
                        d.is_primary
                    FROM DIAGNOSIS d
                    JOIN DISEASE dis ON d.code_icd = dis.code_icd
                    WHERE d.enct_id = %s
                    ORDER BY d.is_primary DESC, d.code_icd;
                    """,
                    (enct_id,),
                )
                return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def list_diagnoses_for_patient(patient_id):
        """
        查詢某位病人的所有診斷（不限就診記錄）。
        包含：就診 ID、ICD 代碼、疾病描述、是否主要診斷、就診時間等。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                desc_field = DiagnosisRepository._get_disease_desc_field(conn)
                
                cur.execute(
                    f"""
                    SELECT
                        d.enct_id,
                        d.code_icd,
                        dis.{desc_field} AS description,
                        d.is_primary,
                        e.encounter_at,
                        e.provider_id,
                        u_provider.name AS provider_name,
                        pr.dept_id,
                        d_dept.name AS department_name
                    FROM DIAGNOSIS d
                    JOIN DISEASE dis ON d.code_icd = dis.code_icd
                    JOIN ENCOUNTER e ON d.enct_id = e.enct_id
                    JOIN APPOINTMENT a ON e.appt_id = a.appt_id
                    JOIN PROVIDER pr ON e.provider_id = pr.user_id
                    JOIN "USER" u_provider ON pr.user_id = u_provider.user_id
                    LEFT JOIN DEPARTMENT d_dept ON pr.dept_id = d_dept.dept_id
                    WHERE a.patient_id = %s
                    ORDER BY e.encounter_at DESC, d.is_primary DESC, d.code_icd;
                    """,
                    (patient_id,),
                )
                return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def upsert_diagnosis(enct_id, code_icd, is_primary):
        """
        新增或更新診斷（以 enct_id + code_icd 為 key）。
        """
        import psycopg2
        conn = get_pg_conn()
        try:
            with conn.cursor() as cur:
                # 先驗證 enct_id 是否存在
                cur.execute(
                    """
                    SELECT enct_id FROM ENCOUNTER WHERE enct_id = %s;
                    """,
                    (enct_id,),
                )
                if cur.fetchone() is None:
                    raise Exception(f"Encounter with enct_id={enct_id} does not exist")
                
                # 驗證 code_icd 是否存在於 DISEASE 表
                cur.execute(
                    """
                    SELECT code_icd FROM DISEASE WHERE code_icd = %s;
                    """,
                    (code_icd,),
                )
                if cur.fetchone() is None:
                    raise Exception(f"Disease with code_icd='{code_icd}' does not exist in DISEASE table")
                
                # 插入或更新診斷
                cur.execute(
                    """
                    INSERT INTO DIAGNOSIS (enct_id, code_icd, is_primary)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (enct_id, code_icd)
                    DO UPDATE SET is_primary = EXCLUDED.is_primary;
                    """,
                    (enct_id, code_icd, is_primary),
                )
                conn.commit()
        except psycopg2.IntegrityError as e:
            conn.rollback()
            # 重新拋出 IntegrityError，讓 service 層處理
            raise e
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def set_primary_diagnosis(enct_id, code_icd):
        """
        將某一個診斷標為主要診斷，同時把同一 enct_id 其他診斷 is_primary 設為 FALSE。
        使用 transaction 確保原子性。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor() as cur:
                # 先確認該診斷是否存在
                cur.execute(
                    """
                    SELECT 1
                    FROM DIAGNOSIS
                    WHERE enct_id = %s AND code_icd = %s;
                    """,
                    (enct_id, code_icd),
                )
                if cur.fetchone() is None:
                    conn.rollback()
                    raise Exception("Diagnosis not found")

                # 將該 encounter 的所有診斷設為非主要診斷
                cur.execute(
                    "UPDATE DIAGNOSIS SET is_primary = FALSE WHERE enct_id = %s;",
                    (enct_id,),
                )
                
                # 將指定診斷設為主要診斷
                cur.execute(
                    """
                    UPDATE DIAGNOSIS
                    SET is_primary = TRUE
                    WHERE enct_id = %s
                      AND code_icd = %s;
                    """,
                    (enct_id, code_icd),
                )
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def search_diseases(query: str = None, limit: int = 50):
        """
        搜尋疾病（ICD 代碼和描述）。
        如果提供 query，則搜尋 code_icd 或描述欄位包含該字串的疾病。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                desc_field = DiagnosisRepository._get_disease_desc_field(conn)
                
                if query:
                    if desc_field == 'code_icd':
                        # 只有 code_icd 欄位，只搜尋 code_icd
                        cur.execute(
                            """
                            SELECT code_icd, code_icd AS description
                            FROM DISEASE
                            WHERE code_icd ILIKE %s
                            ORDER BY code_icd
                            LIMIT %s;
                            """,
                            (f"%{query}%", limit),
                        )
                    else:
                        # 有描述欄位，可以搜尋 code_icd 或描述
                        cur.execute(
                            f"""
                            SELECT code_icd, {desc_field} AS description
                            FROM DISEASE
                            WHERE code_icd ILIKE %s OR {desc_field} ILIKE %s
                            ORDER BY code_icd
                            LIMIT %s;
                            """,
                            (f"%{query}%", f"%{query}%", limit),
                        )
                else:
                    cur.execute(
                        f"""
                        SELECT code_icd, {desc_field} AS description
                        FROM DISEASE
                        ORDER BY code_icd
                        LIMIT %s;
                        """,
                        (limit,),
                    )
                return cur.fetchall()
        finally:
            conn.close()

