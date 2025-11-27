#!/usr/bin/env python3
"""
檢查所有需要序列的表
"""
import psycopg2
from app.config import PG_DSN

def check_table_sequences():
    """檢查所有表的 ID 欄位是否有序列"""
    conn = psycopg2.connect(PG_DSN)
    try:
        cur = conn.cursor()
        
        # 需要檢查的表和 ID 欄位
        tables_to_check = [
            ('USER', 'user_id'),
            ('CLINIC_SESSION', 'session_id'),
            ('APPOINTMENT', 'appt_id'),
            ('ENCOUNTER', 'enct_id'),
            ('PRESCRIPTION', 'presc_id'),
            ('LAB_RESULT', 'lab_id'),
            ('PAYMENT', 'payment_id'),
        ]
        
        print("=== 檢查所有表的 ID 序列 ===\n")
        
        for table_name, id_column in tables_to_check:
            print(f"檢查 {table_name}.{id_column}:")
            
            # 檢查欄位資訊
            cur.execute(f"""
                SELECT column_default, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table_name.lower()}' 
                AND column_name = '{id_column}';
            """)
            result = cur.fetchone()
            
            if result:
                default = result[0]
                nullable = result[1]
                print(f"  Default: {default}")
                print(f"  Nullable: {nullable}")
                
                if default and 'nextval' in str(default):
                    print(f"  ✅ 序列已設定")
                else:
                    print(f"  ❌ 序列未設定，需要修復")
            else:
                print(f"  ⚠️  找不到欄位")
            
            print()
        
        cur.close()
    except Exception as e:
        print(f"錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    check_table_sequences()

