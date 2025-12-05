#!/usr/bin/env python3
"""
修復 CLINIC_SESSION 表的 status CHECK 約束
根據新的資料庫設計，status 只能是 0（停診）或 1（開診）
"""
import psycopg2
from app.config import PG_DSN

def fix_status_constraint():
    """修復 CLINIC_SESSION 表的 status CHECK 約束"""
    conn = psycopg2.connect(PG_DSN)
    try:
        cur = conn.cursor()
        
        # 檢查現有的約束
        cur.execute("""
            SELECT conname, pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = 'clinic_session'::regclass
              AND contype = 'c'
              AND conname LIKE '%status%';
        """)
        constraints = cur.fetchall()
        
        print("現有的 status 相關 CHECK 約束：")
        for conname, condef in constraints:
            print(f"  {conname}: {condef}")
        
        # 刪除現有的 status 約束（如果存在）
        for conname, _ in constraints:
            print(f"\n刪除現有約束: {conname}")
            cur.execute(f"ALTER TABLE clinic_session DROP CONSTRAINT IF EXISTS {conname};")
        
        # 添加新的約束：status 只能是 0 或 1
        print("\n添加新的 CHECK 約束：status IN (0, 1)")
        cur.execute("""
            ALTER TABLE clinic_session
            ADD CONSTRAINT clinic_session_status_check
            CHECK (status IN (0, 1));
        """)
        
        conn.commit()
        print("✅ CHECK 約束已修復")
        
        # 驗證約束
        cur.execute("""
            SELECT conname, pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = 'clinic_session'::regclass
              AND contype = 'c'
              AND conname = 'clinic_session_status_check';
        """)
        result = cur.fetchone()
        if result:
            print(f"\n驗證結果：{result[0]}: {result[1]}")
        
        # 檢查是否有違反約束的資料
        cur.execute("""
            SELECT session_id, provider_id, date, period, capacity, status
            FROM clinic_session
            WHERE status NOT IN (0, 1);
        """)
        invalid_rows = cur.fetchall()
        if invalid_rows:
            print(f"\n⚠️ 發現 {len(invalid_rows)} 筆違反約束的資料：")
            for row in invalid_rows[:10]:  # 只顯示前 10 筆
                print(f"  Session ID: {row[0]}, Status: {row[5]}")
            print("\n建議：將這些資料的 status 更新為 0 或 1")
        else:
            print("\n✅ 所有資料都符合新的約束")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    print("開始修復 CLINIC_SESSION status CHECK 約束...\n")
    fix_status_constraint()
    print("\n腳本執行完成。")

