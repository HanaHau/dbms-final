"""
處理門診結束後未報到的病人，累計爽約次數
此腳本應該定期執行（例如：每小時或每天）
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date, time
from app.config import PG_DSN
from app.repositories import PatientRepository

def process_no_show_appointments():
    """
    處理所有已結束但未報到的掛號：
    - 找出所有已結束的門診時段
    - 找出這些時段中狀態為「已預約」(1) 或「未報到」(5) 的掛號
    - 累計這些病人的爽約次數
    """
    conn = psycopg2.connect(PG_DSN)
    try:
        conn.autocommit = False
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 找出所有已結束的門診時段中，狀態為「已預約」(1) 或「未報到」(5) 的掛號
            cur.execute(
                """
                SELECT DISTINCT a.patient_id, a.appt_id
                FROM APPOINTMENT a
                JOIN CLINIC_SESSION cs ON a.session_id = cs.session_id
                LEFT JOIN LATERAL (
                    SELECT ash.to_status
                    FROM APPOINTMENT_STATUS_HISTORY ash
                    WHERE ash.appt_id = a.appt_id
                    ORDER BY ash.changed_at DESC
                    LIMIT 1
                ) AS ash_latest ON TRUE
                WHERE COALESCE(ash_latest.to_status, 1) IN (1, 5)  -- 已預約或未報到
                  AND (cs.date < CURRENT_DATE 
                       OR (cs.date = CURRENT_DATE AND cs.end_time < CURRENT_TIME))
                  AND NOT EXISTS (
                      -- 排除已經處理過的（已經有就診記錄的）
                      SELECT 1 FROM ENCOUNTER e WHERE e.appt_id = a.appt_id
                  )
                  AND NOT EXISTS (
                      -- 排除已經累計過爽約次數的（檢查是否有標記）
                      SELECT 1 FROM APPOINTMENT_STATUS_HISTORY ash2
                      WHERE ash2.appt_id = a.appt_id
                        AND ash2.to_status = 5
                        AND ash2.changed_at > (
                            SELECT MAX(cs2.date + cs2.end_time)
                            FROM CLINIC_SESSION cs2
                            WHERE cs2.session_id = a.session_id
                        )
                  );
                """,
            )
            
            no_show_appointments = cur.fetchall()
            
            processed_count = 0
            for row in no_show_appointments:
                patient_id = row["patient_id"]
                appt_id = row["appt_id"]
                
                # 累計爽約次數
                PatientRepository.increment_no_show_count(patient_id)
                
                # 將掛號狀態更新為「未報到」(5)
                from app.repositories import AppointmentRepository
                appointment = AppointmentRepository.get_appointment_by_id(appt_id)
                if appointment:
                    cur.execute(
                        """
                        SELECT provider_id FROM CLINIC_SESSION
                        WHERE session_id = %s;
                        """,
                        (appointment["session_id"],)
                    )
                    session_row = cur.fetchone()
                    if session_row:
                        provider_id = session_row["provider_id"]
                        current_status = AppointmentRepository._get_latest_status(conn, appt_id)
                        if current_status != 5:  # 如果還不是未報到狀態
                            AppointmentRepository._insert_status_history(
                                conn, appt_id, current_status, 5, provider_id
                            )
                
                processed_count += 1
            
            conn.commit()
            print(f"✅ 已處理 {processed_count} 個未報到的掛號")
            return processed_count
            
    except Exception as e:
        conn.rollback()
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    print("============================================================")
    print("處理門診結束後未報到的病人，累計爽約次數")
    print("============================================================")
    count = process_no_show_appointments()
    print(f"\n處理完成，共處理 {count} 個未報到的掛號。")

