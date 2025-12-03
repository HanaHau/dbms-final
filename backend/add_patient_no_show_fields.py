"""
添加 PATIENT 表的 no_show_count 和 banned_until 欄位
"""
import psycopg2
from app.config import PG_DSN

def add_patient_no_show_fields():
    conn = psycopg2.connect(PG_DSN)
    try:
        cur = conn.cursor()
        
        # 檢查並添加 no_show_count 欄位
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'patient' AND column_name = 'no_show_count';
        """)
        if cur.fetchone() is None:
            print("添加 no_show_count 欄位...")
            cur.execute("""
                ALTER TABLE PATIENT
                ADD COLUMN no_show_count INTEGER DEFAULT 0;
            """)
            print("✅ no_show_count 欄位已添加")
        else:
            print("ℹ️ no_show_count 欄位已存在")
        
        # 檢查並添加 banned_until 欄位
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'patient' AND column_name = 'banned_until';
        """)
        if cur.fetchone() is None:
            print("添加 banned_until 欄位...")
            cur.execute("""
                ALTER TABLE PATIENT
                ADD COLUMN banned_until DATE;
            """)
            print("✅ banned_until 欄位已添加")
        else:
            print("ℹ️ banned_until 欄位已存在")
        
        conn.commit()
        print("\n✅ 所有欄位檢查完成")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    print("============================================================")
    print("添加 PATIENT 表的 no_show_count 和 banned_until 欄位")
    print("============================================================")
    add_patient_no_show_fields()
    print("\n腳本執行完成。")

