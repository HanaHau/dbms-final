#!/usr/bin/env python3
"""
修復 PRESCRIPTION 表的 rx_id 序列問題
"""
import psycopg2
from app.config import PG_DSN

def fix_prescription_rx_id_sequence():
    """修復 prescription.rx_id 的序列設定"""
    conn = psycopg2.connect(PG_DSN)
    try:
        cur = conn.cursor()
        
        # 檢查序列是否存在
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_sequences WHERE sequencename = 'prescription_rx_id_seq'
            );
        """)
        seq_exists = cur.fetchone()[0]
        
        if not seq_exists:
            print("建立序列 prescription_rx_id_seq...")
            
            # 取得現有的最大 rx_id
            cur.execute('SELECT COALESCE(MAX(rx_id), 0) FROM prescription;')
            max_id = cur.fetchone()[0]
            start_value = max_id + 1
            
            print(f"當前最大 rx_id: {max_id}, 序列起始值: {start_value}")
            
            # 建立序列
            cur.execute(f"""
                CREATE SEQUENCE prescription_rx_id_seq START {start_value};
            """)
            
            # 設定序列為 rx_id 的 DEFAULT
            cur.execute("""
                ALTER TABLE prescription 
                ALTER COLUMN rx_id SET DEFAULT nextval('prescription_rx_id_seq');
            """)
            
            # 將序列的所有權給 prescription 表
            cur.execute("""
                ALTER SEQUENCE prescription_rx_id_seq OWNED BY prescription.rx_id;
            """)
            
            conn.commit()
            print(f"✅ 序列已建立，起始值為 {start_value}")
        else:
            print("序列已存在，檢查設定...")
            
            # 檢查 DEFAULT 是否正確設定
            cur.execute("""
                SELECT column_default
                FROM information_schema.columns
                WHERE table_name = 'prescription' AND column_name = 'rx_id';
            """)
            result = cur.fetchone()
            
            if result and result[0] and 'nextval' in str(result[0]):
                print("✅ 序列已正確設定")
            else:
                print("設定 DEFAULT...")
                # 設定 DEFAULT
                cur.execute("""
                    ALTER TABLE prescription 
                    ALTER COLUMN rx_id SET DEFAULT nextval('prescription_rx_id_seq');
                """)
                conn.commit()
                print("✅ DEFAULT 已設定")
        
        # 驗證設定
        cur.execute("""
            SELECT column_name, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'prescription' AND column_name = 'rx_id';
        """)
        result = cur.fetchone()
        if result:
            print(f"\n驗證結果:")
            print(f"  欄位名稱: {result[0]}")
            print(f"  Default: {result[1]}")
            print(f"  Nullable: {result[2]}")
        
        cur.close()
    except Exception as e:
        conn.rollback()
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    print("============================================================")
    print("修復 PRESCRIPTION 表的 rx_id 序列")
    print("============================================================")
    fix_prescription_rx_id_sequence()
    print("\n腳本執行完成。")

