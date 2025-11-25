# repositories/payment_repo.py
from psycopg2.extras import RealDictCursor
from ..pg_base import get_pg_conn


class PaymentRepository:
    """處理繳費（PAYMENT）相關的資料庫操作"""

    @staticmethod
    def get_payment_for_encounter(enct_id):
        """
        查詢某次就診的繳費資訊。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        payment_id,
                        enct_id,
                        amount,
                        method,
                        invoice_no,
                        paid_at
                    FROM PAYMENT
                    WHERE enct_id = %s;
                    """,
                    (enct_id,),
                )
                return cur.fetchone()
        finally:
            conn.close()

    @staticmethod
    def list_payments_for_patient(patient_id):
        """
        查詢某位病人的所有繳費記錄。
        包含：繳費 ID、就診 ID、金額、付款方式、發票號碼等。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        pay.payment_id,
                        pay.enct_id,
                        pay.amount,
                        pay.method,
                        pay.invoice_no,
                        pay.paid_at,
                        e.encounter_at,
                        e.provider_id,
                        u_provider.name AS provider_name,
                        pr.dept_id,
                        d.name AS department_name
                    FROM PAYMENT pay
                    JOIN ENCOUNTER e ON pay.enct_id = e.enct_id
                    JOIN APPOINTMENT a ON e.appt_id = a.appt_id
                    JOIN PROVIDER pr ON e.provider_id = pr.user_id
                    JOIN "USER" u_provider ON pr.user_id = u_provider.user_id
                    LEFT JOIN DEPARTMENT d ON pr.dept_id = d.dept_id
                    WHERE a.patient_id = %s
                    ORDER BY e.encounter_at DESC, pay.paid_at DESC;
                    """,
                    (patient_id,),
                )
                return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def upsert_payment_for_encounter(enct_id, amount, method, invoice_no):
        """
        建立或更新某次就診的費用資料（假設一個 encounter 只會有一筆 PAYMENT）。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT payment_id FROM PAYMENT WHERE enct_id = %s;",
                    (enct_id,),
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        """
                        INSERT INTO PAYMENT (
                            enct_id, amount, method, invoice_no, paid_at
                        )
                        VALUES (%s, %s, %s, %s, NOW())
                        RETURNING payment_id, enct_id, amount, method, invoice_no, paid_at;
                        """,
                        (enct_id, amount, method, invoice_no),
                    )
                else:
                    payment_id = row["payment_id"]
                    cur.execute(
                        """
                        UPDATE PAYMENT
                        SET amount    = %s,
                            method    = %s,
                            invoice_no = %s
                        WHERE payment_id = %s
                        RETURNING payment_id, enct_id, amount, method, invoice_no, paid_at;
                        """,
                        (amount, method, invoice_no, payment_id),
                    )

                result = cur.fetchone()
                conn.commit()
                return result
        finally:
            conn.close()

