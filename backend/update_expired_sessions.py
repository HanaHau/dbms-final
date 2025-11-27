#!/usr/bin/env python3
"""
更新所有已過期的門診時段狀態為停診（status = 0）
"""
import psycopg2
from app.config import PG_DSN

def update_expired_sessions():
    """更新所有已過期的門診時段"""
    conn = psycopg2.connect(PG_DSN)
    try:
        cur = conn.cursor()
        
        # 更新所有已過期的 session
        cur.execute(
            """
            UPDATE CLINIC_SESSION
            SET status = 0
            WHERE status = 1
              AND (date < CURRENT_DATE 
                   OR (date = CURRENT_DATE AND end_time < CURRENT_TIME));
            """
        )
        
        updated_count = cur.rowcount
        conn.commit()
        
        print(f"✅ 已更新 {updated_count} 個過期的門診時段")
        
        # 顯示更新的 session
        if updated_count > 0:
            cur.execute(
                """
                SELECT session_id, provider_id, date, start_time, end_time, status
                FROM CLINIC_SESSION
                WHERE status = 0
                  AND (date < CURRENT_DATE 
                       OR (date = CURRENT_DATE AND end_time < CURRENT_TIME))
                ORDER BY date DESC, end_time DESC
                LIMIT 10;
                """
            )
            rows = cur.fetchall()
            print("\n最近更新的門診時段：")
            for row in rows:
                print(f"  Session ID: {row[0]}, Provider: {row[1]}, Date: {row[2]}, Time: {row[3]}-{row[4]}, Status: {row[5]}")
        
        cur.close()
    except Exception as e:
        conn.rollback()
        print(f"❌ 錯誤: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("開始更新過期的門診時段...\n")
    update_expired_sessions()

