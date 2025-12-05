# repositories/prescription_repo.py
from psycopg2.extras import RealDictCursor
from ..pg_base import get_pg_conn


class PrescriptionRepository:
    """處理處方與用藥（PRESCRIPTION + INCLUDE）相關的資料庫操作"""

    @staticmethod
    def get_prescription_for_encounter(enct_id):
        """
        查詢某次就診的處方箋（若有的話，包含用藥明細）。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT rx_id, enct_id, status
                    FROM PRESCRIPTION
                    WHERE enct_id = %s;
                    """,
                    (enct_id,),
                )
                header = cur.fetchone()
                if header is None:
                    return None

                rx_id = header["rx_id"]

                cur.execute(
                    """
                    SELECT
                        inc.rx_id,
                        inc.med_id,
                        m.name AS med_name,
                        m.spec,
                        m.unit,
                        inc.dosage,
                        inc.frequency,
                        inc.days,
                        inc.quantity
                    FROM INCLUDE inc
                    JOIN MEDICATION m ON inc.med_id = m.med_id
                    WHERE inc.rx_id = %s
                    ORDER BY m.name;
                    """,
                    (rx_id,),
                )
                items = cur.fetchall()
                header["items"] = items
                return header
        finally:
            conn.close()

    @staticmethod
    def upsert_prescription_for_encounter(enct_id, status=1):
        """
        建立或更新某次就診的處方箋（只管 PRESCRIPTION；INCLUDE 由 replace_prescription_items 負責）。
        status: 1=草稿，2=已定稿
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT rx_id, status FROM PRESCRIPTION WHERE enct_id = %s;",
                    (enct_id,),
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        """
                        INSERT INTO PRESCRIPTION (enct_id, status)
                        VALUES (%s, %s)
                        RETURNING rx_id, enct_id, status;
                        """,
                        (enct_id, status),
                    )
                else:
                    rx_id = row["rx_id"]
                    current_status = row["status"]
                    # 如果處方已定稿（status=2），不允許修改（除非是要定稿，但這應該不會發生）
                    if current_status == 2 and status != 2:
                        raise Exception("處方已定稿，無法修改")
                    # 如果處方是草稿（status=1），允許更新狀態（包括定稿為 status=2）
                    cur.execute(
                        """
                        UPDATE PRESCRIPTION
                        SET status = %s
                        WHERE rx_id = %s
                        RETURNING rx_id, enct_id, status;
                        """,
                        (status, rx_id),
                    )

                result = cur.fetchone()
                conn.commit()
                return result
        finally:
            conn.close()

    @staticmethod
    def replace_prescription_items(rx_id, items):
        """
        重建某張處方箋的所有用藥內容：
        - 先 DELETE 原本的 INCLUDE
        - 再根據 items INSERT 新的
        items 每個元素預期包含：
            med_id, dosage, frequency, days, quantity
        """
        conn = get_pg_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM INCLUDE WHERE rx_id = %s;", (rx_id,))

                for item in items:
                    cur.execute(
                        """
                        INSERT INTO INCLUDE (
                            rx_id, med_id, dosage, frequency, days, quantity
                        )
                        VALUES (%s, %s, %s, %s, %s, %s);
                        """,
                        (
                            rx_id,
                            item["med_id"],
                            item.get("dosage"),
                            item.get("frequency"),
                            item["days"],
                            item["quantity"],
                        ),
                    )

                conn.commit()
        finally:
            conn.close()

    @staticmethod
    def list_prescriptions_for_patient(patient_id):
        """
        查詢某位病人的所有處方箋（優化版本）。
        包含：處方 ID、就診 ID、用藥明細等。
        使用批量查詢避免 N+1 問題。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 查詢所有處方摘要
                cur.execute(
                    """
                    SELECT
                        rx.rx_id,
                        rx.enct_id,
                        e.encounter_at,
                        e.provider_id,
                        u_provider.name AS provider_name,
                        pr.dept_id,
                        d.name AS department_name
                    FROM PRESCRIPTION rx
                    JOIN ENCOUNTER e ON rx.enct_id = e.enct_id
                    JOIN APPOINTMENT a ON e.appt_id = a.appt_id
                    JOIN PROVIDER pr ON e.provider_id = pr.user_id
                    JOIN "USER" u_provider ON pr.user_id = u_provider.user_id
                    LEFT JOIN DEPARTMENT d ON pr.dept_id = d.dept_id
                    WHERE a.patient_id = %s
                    ORDER BY e.encounter_at DESC;
                    """,
                    (patient_id,),
                )
                prescriptions = cur.fetchall()

                if not prescriptions:
                    return []

                # 取得所有處方 ID
                rx_ids = [rx["rx_id"] for rx in prescriptions]

                # 一次查詢所有用藥明細（避免 N 次查詢）
                cur.execute(
                    """
                    SELECT
                        inc.rx_id,
                        inc.med_id,
                        m.name AS med_name,
                        m.spec,
                        m.unit,
                        inc.dosage,
                        inc.frequency,
                        inc.days,
                        inc.quantity
                    FROM INCLUDE inc
                    JOIN MEDICATION m ON inc.med_id = m.med_id
                    WHERE inc.rx_id = ANY(%s)
                    ORDER BY inc.rx_id, m.name;
                    """,
                    (rx_ids,),
                )
                all_items = cur.fetchall()

                # 建立 rx_id -> items 的映射
                items_map = {}
                for item in all_items:
                    rx_id = item["rx_id"]
                    if rx_id not in items_map:
                        items_map[rx_id] = []
                    items_map[rx_id].append(item)

                # 將用藥明細分配到對應的處方
                for rx in prescriptions:
                    rx["items"] = items_map.get(rx["rx_id"], [])

                return prescriptions
        finally:
            conn.close()

    @staticmethod
    def list_prescriptions_for_encounters(enct_ids):
        """
        批量查詢多個就診的處方（優化版本）。
        使用 enct_id 列表，避免重複 JOIN APPOINTMENT 表。
        同時一次性查詢所有用藥明細，避免 N 次查詢。
        """
        if not enct_ids:
            return []
        
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 一次查詢所有處方摘要
                cur.execute(
                    """
                    SELECT
                        rx.rx_id,
                        rx.enct_id,
                        rx.status
                    FROM PRESCRIPTION rx
                    WHERE rx.enct_id = ANY(%s)
                    ORDER BY rx.enct_id;
                    """,
                    (enct_ids,),
                )
                prescriptions = cur.fetchall()
                
                if not prescriptions:
                    return []
                
                # 取得所有處方 ID
                rx_ids = [rx["rx_id"] for rx in prescriptions]
                
                # 一次查詢所有用藥明細（避免 N 次查詢）
                cur.execute(
                    """
                    SELECT
                        inc.rx_id,
                        inc.med_id,
                        m.name AS med_name,
                        m.spec,
                        m.unit,
                        inc.dosage,
                        inc.frequency,
                        inc.days,
                        inc.quantity
                    FROM INCLUDE inc
                    JOIN MEDICATION m ON inc.med_id = m.med_id
                    WHERE inc.rx_id = ANY(%s)
                    ORDER BY inc.rx_id, m.name;
                    """,
                    (rx_ids,),
                )
                all_items = cur.fetchall()
                
                # 建立 rx_id -> items 的映射
                items_map = {}
                for item in all_items:
                    rx_id = item["rx_id"]
                    if rx_id not in items_map:
                        items_map[rx_id] = []
                    items_map[rx_id].append(item)
                
                # 將用藥明細分配到對應的處方
                for rx in prescriptions:
                    rx_id = rx["rx_id"]
                    rx["items"] = items_map.get(rx_id, [])
                
                return prescriptions
        finally:
            conn.close()

    @staticmethod
    def search_medications(query: str = None, limit: int = 50):
        """
        搜尋藥品（med_id 和 name）。
        如果提供 query，則搜尋 med_id 或 name 包含該字串的藥品。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if query:
                    cur.execute(
                        """
                        SELECT med_id, name, spec, unit
                        FROM MEDICATION
                        WHERE CAST(med_id AS TEXT) ILIKE %s OR name ILIKE %s
                        ORDER BY med_id
                        LIMIT %s;
                        """,
                        (f"%{query}%", f"%{query}%", limit),
                    )
                else:
                    cur.execute(
                        """
                        SELECT med_id, name, spec, unit
                        FROM MEDICATION
                        ORDER BY med_id
                        LIMIT %s;
                        """,
                        (limit,),
                    )
                return cur.fetchall()
        finally:
            conn.close()

