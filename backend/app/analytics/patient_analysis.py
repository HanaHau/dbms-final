# analytics/patient_analysis.py
import duckdb
from ..config import PG_URI

DUCKDB_FILE = "clinic_analytics.duckdb"


def get_duckdb_conn():
    """
    初始化 DuckDB 連接並設置 PostgreSQL 掃描器。
    - 啟用 postgres_scanner extension
    - 將 PostgreSQL 主庫附掛為 pgdb source（唯讀，僅用於查詢）
    """
    con = duckdb.connect(DUCKDB_FILE)
    # 啟用 postgres_scanner extension
    con.execute("INSTALL postgres_scanner")
    con.execute("LOAD postgres_scanner")
    # 把 PostgreSQL 附掛成 pgdb（用於唯讀查詢）
    con.execute(f"ATTACH '{PG_URI}' AS pgdb (TYPE POSTGRES)")
    return con


def get_patient_statistics(patient_id: int):
    """
    取得病人的統計資料：
    - 年度就診次數
    - 各科別就診分布
    - 常見診斷 top 10
    
    Args:
        patient_id: 病人 ID
    
    Returns:
        dict: 包含統計資料的字典
    """
    con = get_duckdb_conn()
    
    try:
        # 1. 年度就診次數
        annual_visits_query = """
            SELECT
                EXTRACT(YEAR FROM e.encounter_at) AS year,
                COUNT(*) AS visit_count
            FROM pgdb.public.ENCOUNTER e
            JOIN pgdb.public.APPOINTMENT a ON e.appt_id = a.appt_id
            WHERE a.patient_id = ?
            GROUP BY EXTRACT(YEAR FROM e.encounter_at)
            ORDER BY year DESC;
        """
        annual_visits_df = con.execute(annual_visits_query, [patient_id]).df()
        annual_visits = annual_visits_df.to_dict('records') if not annual_visits_df.empty else []
        
        # 2. 各科別就診分布
        department_distribution_query = """
            SELECT
                d.dept_id,
                d.name AS department_name,
                COUNT(*) AS visit_count
            FROM pgdb.public.ENCOUNTER e
            JOIN pgdb.public.APPOINTMENT a ON e.appt_id = a.appt_id
            JOIN pgdb.public.PROVIDER pr ON e.provider_id = pr.user_id
            JOIN pgdb.public.DEPARTMENT d ON pr.dept_id = d.dept_id
            WHERE a.patient_id = ?
            GROUP BY d.dept_id, d.name
            ORDER BY visit_count DESC;
        """
        department_distribution_df = con.execute(department_distribution_query, [patient_id]).df()
        department_distribution = department_distribution_df.to_dict('records') if not department_distribution_df.empty else []
        
        # 3. 常見診斷 top 10
        top_diagnoses_query = """
            SELECT
                d.code_icd,
                dis.description AS diagnosis_description,
                COUNT(*) AS diagnosis_count
            FROM pgdb.public.DIAGNOSIS d
            JOIN pgdb.public.ENCOUNTER e ON d.enct_id = e.enct_id
            JOIN pgdb.public.APPOINTMENT a ON e.appt_id = a.appt_id
            JOIN pgdb.public.DISEASE dis ON d.code_icd = dis.code_icd
            WHERE a.patient_id = ?
            GROUP BY d.code_icd, dis.description
            ORDER BY diagnosis_count DESC
            LIMIT 10;
        """
        top_diagnoses_df = con.execute(top_diagnoses_query, [patient_id]).df()
        top_diagnoses = top_diagnoses_df.to_dict('records') if not top_diagnoses_df.empty else []
        
        return {
            "patient_id": patient_id,
            "annual_visits": annual_visits,
            "department_distribution": department_distribution,
            "top_diagnoses": top_diagnoses,
        }
    finally:
        con.close()

