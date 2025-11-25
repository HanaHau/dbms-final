# pg_provider.py
from psycopg2.extras import RealDictCursor
from psycopg2 import IntegrityError

from .pg_base import get_pg_conn, generate_new_id


# ==============================
# 1. 醫師註冊 / 基本資料
# ==============================

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
            # 新的 user_id
            new_user_id = generate_new_id(conn, '"USER"', "user_id")

            # USER
            cur.execute(
                """
                INSERT INTO "USER" (user_id, name, hash_pwd, type)
                VALUES (%s, %s, %s, 'provider')
                """,
                (new_user_id, name, hash_pwd),
            )

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
    finally:
        conn.close()

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


# ==============================
# 2. 門診時段排程與維護（CLINIC_SESSION）
# ==============================

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


def create_clinic_session(provider_user_id, date_, start_time_, end_time_, capacity):
    """
    醫師新增門診時段。
    status 預設為 1（例如：尚未開始）。
    """
    conn = get_pg_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            new_session_id = generate_new_id(conn, "CLINIC_SESSION", "session_id")
            cur.execute(
                """
                INSERT INTO CLINIC_SESSION (
                    session_id, provider_id, date, start_time, end_time, capacity, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, 1)
                RETURNING session_id, provider_id, date, start_time, end_time, capacity, status;
                """,
                (new_session_id, provider_user_id, date_, start_time_, end_time_, capacity),
            )
            conn.commit()
            return cur.fetchone()
    finally:
        conn.close()


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


# ==============================
# 3. 門診病人清單管理（APPOINTMENT）
# ==============================

def list_appointments_for_session(provider_user_id, session_id):
    """
    列出某個門診時段的掛號清單（只允許看自己的 session）。
    包含：病人姓名、slot_seq、目前掛號狀態。
    狀態來自 APPOINTMENT_STATUS_HISTORY 最新一筆 to_status。
    """
    conn = get_pg_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    a.appt_id,
                    a.slot_seq,
                    p.user_id             AS patient_id,
                    u_pt.name             AS patient_name,
                    ash_latest.to_status  AS status,
                    ash_latest.changed_at AS status_changed_at
                FROM CLINIC_SESSION cs
                JOIN APPOINTMENT a   ON a.session_id = cs.session_id
                JOIN PATIENT p       ON a.patient_id = p.user_id
                JOIN "USER" u_pt     ON p.user_id = u_pt.user_id
                LEFT JOIN LATERAL (
                    SELECT ash.to_status, ash.changed_at
                    FROM APPOINTMENT_STATUS_HISTORY ash
                    WHERE ash.appt_id = a.appt_id
                    ORDER BY ash.changed_at DESC
                    LIMIT 1
                ) AS ash_latest ON TRUE
                WHERE cs.session_id = %s
                  AND cs.provider_id = %s
                ORDER BY a.slot_seq;
                """,
                (session_id, provider_user_id),
            )
            return cur.fetchall()
    finally:
        conn.close()


def update_appointment_status(provider_user_id, appt_id, new_status):
    """
    醫師更新掛號狀態：
    - 查目前最新狀態作為 from_status
    - 寫一筆新的 APPOINTMENT_STATUS_HISTORY
    """
    conn = get_pg_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT to_status
                FROM APPOINTMENT_STATUS_HISTORY
                WHERE appt_id = %s
                ORDER BY changed_at DESC
                LIMIT 1;
                """,
                (appt_id,),
            )
            row = cur.fetchone()
            from_status = row["to_status"] if row is not None else None

            cur.execute(
                """
                INSERT INTO APPOINTMENT_STATUS_HISTORY (
                    appt_id, from_status, to_status, changed_by, changed_at
                )
                VALUES (%s, %s, %s, %s, NOW());
                """,
                (appt_id, from_status, new_status, provider_user_id),
            )
            conn.commit()
    finally:
        conn.close()


# ==============================
# 4. 就診紀錄（ENCOUNTER）
# ==============================

def get_encounter_by_appt(provider_user_id, appt_id):
    """
    查詢某筆掛號對應的就診紀錄（只看自己的 encounter）。
    """
    conn = get_pg_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    e.enct_id,
                    e.appt_id,
                    e.provider_id,
                    e.encounter_at,
                    e.status,
                    e.chief_complaint,
                    e.subjective,
                    e.assessment,
                    e.plan
                FROM ENCOUNTER e
                WHERE e.appt_id = %s
                  AND e.provider_id = %s;
                """,
                (appt_id, provider_user_id),
            )
            return cur.fetchone()
    finally:
        conn.close()


def upsert_encounter(
    provider_user_id,
    appt_id,
    status,
    chief_complaint,
    subjective,
    assessment,
    plan,
):
    """
    新增或更新就診紀錄：
    - 若該 provider + appt 還沒有 ENCOUNTER，就插入一筆
    - 否則更新內容（支援草稿 / 定稿）
    """
    conn = get_pg_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT enct_id
                FROM ENCOUNTER
                WHERE appt_id = %s
                  AND provider_id = %s;
                """,
                (appt_id, provider_user_id),
            )
            row = cur.fetchone()

            if row is None:
                new_enct_id = generate_new_id(conn, "ENCOUNTER", "enct_id")
                cur.execute(
                    """
                    INSERT INTO ENCOUNTER (
                        enct_id, appt_id, provider_id, encounter_at,
                        status, chief_complaint, subjective, assessment, plan
                    )
                    VALUES (%s, %s, %s, NOW(),
                            %s, %s, %s, %s, %s)
                    RETURNING enct_id, appt_id, provider_id, encounter_at,
                              status, chief_complaint, subjective, assessment, plan;
                    """,
                    (
                        new_enct_id,
                        appt_id,
                        provider_user_id,
                        status,
                        chief_complaint,
                        subjective,
                        assessment,
                        plan,
                    ),
                )
            else:
                enct_id = row["enct_id"]
                cur.execute(
                    """
                    UPDATE ENCOUNTER
                    SET status          = %s,
                        chief_complaint = %s,
                        subjective      = %s,
                        assessment      = %s,
                        plan            = %s
                    WHERE enct_id = %s
                      AND provider_id = %s
                    RETURNING enct_id, appt_id, provider_id, encounter_at,
                              status, chief_complaint, subjective, assessment, plan;
                    """,
                    (
                        status,
                        chief_complaint,
                        subjective,
                        assessment,
                        plan,
                        enct_id,
                        provider_user_id,
                    ),
                )

            result = cur.fetchone()
            conn.commit()
            return result
    finally:
        conn.close()


# ==============================
# 5. 診斷（DIAGNOSIS）
# ==============================

def list_diagnoses_for_encounter(enct_id):
    """
    查詢一個就診紀錄的所有診斷。
    """
    conn = get_pg_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    d.enct_id,
                    d.code_icd,
                    dis.description,
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


def upsert_diagnosis(enct_id, code_icd, is_primary):
    """
    新增或更新診斷（以 enct_id + code_icd 為 key）。
    """
    conn = get_pg_conn()
    try:
        with conn.cursor() as cur:
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
    finally:
        conn.close()


def set_primary_diagnosis(enct_id, code_icd):
    """
    將某一個診斷標為主要診斷，同時把同一 enct_id 其他診斷 is_primary 設為 FALSE。
    """
    conn = get_pg_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE DIAGNOSIS SET is_primary = FALSE WHERE enct_id = %s;",
                (enct_id,),
            )
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
    finally:
        conn.close()


# ==============================
# 6. 檢驗結果（LAB_RESULT）
# ==============================

def list_lab_results_for_encounter(enct_id):
    """
    查詢某次就診的所有檢驗結果。
    """
    conn = get_pg_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    lab_id,
                    enct_id,
                    loinc_code,
                    item_name,
                    value,
                    unit,
                    ref_low,
                    ref_high,
                    abnormal_flag,
                    reported_at
                FROM LAB_RESULT
                WHERE enct_id = %s
                ORDER BY reported_at NULLS LAST, lab_id;
                """,
                (enct_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def add_lab_result(
    enct_id,
    loinc_code,
    item_name,
    value,
    unit,
    ref_low,
    ref_high,
    abnormal_flag,
    reported_at,
):
    """
    新增一筆檢驗結果。
    """
    conn = get_pg_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            new_lab_id = generate_new_id(conn, "LAB_RESULT", "lab_id")
            cur.execute(
                """
                INSERT INTO LAB_RESULT (
                    lab_id, enct_id, loinc_code, item_name,
                    value, unit, ref_low, ref_high, abnormal_flag, reported_at
                )
                VALUES (%s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s)
                RETURNING lab_id, enct_id, loinc_code, item_name,
                          value, unit, ref_low, ref_high, abnormal_flag, reported_at;
                """,
                (
                    new_lab_id,
                    enct_id,
                    loinc_code,
                    item_name,
                    value,
                    unit,
                    ref_low,
                    ref_high,
                    abnormal_flag,
                    reported_at,
                ),
            )
            conn.commit()
            return cur.fetchone()
    finally:
        conn.close()


# ==============================
# 7. 處方與用藥（PRESCRIPTION + INCLUDE）
# ==============================

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


def upsert_prescription_for_encounter(enct_id, status):
    """
    建立或更新某次就診的處方箋（只管 PRESCRIPTION；INCLUDE 由 replace_prescription_items 負責）。
    """
    conn = get_pg_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT rx_id FROM PRESCRIPTION WHERE enct_id = %s;",
                (enct_id,),
            )
            row = cur.fetchone()
            if row is None:
                new_rx_id = generate_new_id(conn, "PRESCRIPTION", "rx_id")
                cur.execute(
                    """
                    INSERT INTO PRESCRIPTION (rx_id, enct_id, status)
                    VALUES (%s, %s, %s)
                    RETURNING rx_id, enct_id, status;
                    """,
                    (new_rx_id, enct_id, status),
                )
            else:
                rx_id = row["rx_id"]
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


# ==============================
# 8. 繳費（PAYMENT）
# ==============================

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
                new_payment_id = generate_new_id(conn, "PAYMENT", "payment_id")
                cur.execute(
                    """
                    INSERT INTO PAYMENT (
                        payment_id, enct_id, amount, method, invoice_no, paid_at
                    )
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    RETURNING payment_id, enct_id, amount, method, invoice_no, paid_at;
                    """,
                    (new_payment_id, enct_id, amount, method, invoice_no),
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


# ==============================
# 9. 醫師查詢病患完整病歷（只看自己看過的）
# ==============================

def list_encounters_for_patient_by_provider(provider_user_id, patient_user_id):
    """
    醫師查詢某位病患在「自己」這裡的所有就診紀錄，
    供完整病歷查詢與追蹤使用。
    """
    conn = get_pg_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    e.enct_id,
                    e.encounter_at,
                    e.status,
                    e.chief_complaint,
                    e.assessment,
                    e.plan,
                    a.appt_id,
                    cs.date       AS session_date,
                    cs.start_time AS session_start_time
                FROM ENCOUNTER e
                JOIN APPOINTMENT a   ON e.appt_id = a.appt_id
                JOIN CLINIC_SESSION cs ON a.session_id = cs.session_id
                WHERE e.provider_id = %s
                  AND a.patient_id  = %s
                ORDER BY e.encounter_at DESC;
                """,
                (provider_user_id, patient_user_id),
            )
            return cur.fetchall()
    finally:
        conn.close()
