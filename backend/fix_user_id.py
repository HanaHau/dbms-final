#!/usr/bin/env python3
"""
修復 USER 表的 user_id 自動遞增問題
"""
import psycopg2
from app.config import PG_DSN

def fix_user_id_sequence():
    """修復 user_id 的序列設定"""
    conn = psycopg2.connect(PG_DSN)
    try:
        cur = conn.cursor()
        
        # 檢查是否已有序列
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_sequences WHERE sequencename = 'user_user_id_seq'
            );
        """)
        seq_exists = cur.fetchone()[0]
        
        if not seq_exists:
            print("建立序列 user_user_id_seq...")
            
            # 取得現有的最大 user_id
            cur.execute('SELECT COALESCE(MAX(user_id), 0) FROM "USER";')
            max_id = cur.fetchone()[0]
            start_value = max_id + 1
            
            # 建立序列
            cur.execute(f"""
                CREATE SEQUENCE user_user_id_seq START {start_value};
            """)
            
            # 設定序列為 user_id 的 DEFAULT
            cur.execute("""
                ALTER TABLE "USER" 
                ALTER COLUMN user_id SET DEFAULT nextval('user_user_id_seq');
            """)
            
            # 將序列的所有權給 USER 表
            cur.execute("""
                ALTER SEQUENCE user_user_id_seq OWNED BY "USER".user_id;
            """)
            
            conn.commit()
            print(f"✅ 序列已建立，起始值為 {start_value}")
        else:
            print("序列已存在，檢查設定...")
            
            # 檢查 DEFAULT 是否正確設定
            cur.execute("""
                SELECT column_default
                FROM information_schema.columns
                WHERE table_name = 'USER' AND column_name = 'user_id';
            """)
            default = cur.fetchone()[0]
            
            if default and 'nextval' in default:
                print("✅ DEFAULT 已正確設定")
            else:
                print("⚠️  DEFAULT 未設定，正在設定...")
                cur.execute("""
                    ALTER TABLE "USER" 
                    ALTER COLUMN user_id SET DEFAULT nextval('user_user_id_seq');
                """)
                conn.commit()
                print("✅ DEFAULT 已設定")
        
        # 驗證設定
        cur.execute("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'USER' AND column_name = 'user_id';
        """)
        result = cur.fetchone()
        print(f"\n驗證結果:")
        print(f"  欄位名稱: {result[0]}")
        print(f"  資料類型: {result[1]}")
        print(f"  預設值: {result[2]}")
        print(f"  可為空: {result[3]}")
        
        cur.close()
    except Exception as e:
        conn.rollback()
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    print("開始修復 USER 表的 user_id 序列...")
    fix_user_id_sequence()
    print("\n修復完成！現在可以重新測試註冊功能。")

