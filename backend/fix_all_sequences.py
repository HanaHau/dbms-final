#!/usr/bin/env python3
"""
修復所有表的 ID 序列問題
"""
import psycopg2
from app.config import PG_DSN

def fix_sequence(table_name, id_column, sequence_name, use_quotes=True):
    """修復單個表的序列"""
    conn = psycopg2.connect(PG_DSN)
    try:
        cur = conn.cursor()
        
        # 檢查序列是否存在
        cur.execute(f"""
            SELECT EXISTS (
                SELECT 1 FROM pg_sequences WHERE sequencename = '{sequence_name}'
            );
        """)
        seq_exists = cur.fetchone()[0]
        
        if not seq_exists:
            # 取得現有的最大 ID
            table_ref = f'"{table_name}"' if use_quotes else table_name
            cur.execute(f'SELECT COALESCE(MAX({id_column}), 0) FROM {table_ref};')
            max_id = cur.fetchone()[0]
            start_value = max_id + 1
            
            # 建立序列
            cur.execute(f"""
                CREATE SEQUENCE {sequence_name} START {start_value};
            """)
            
            # 設定序列為 ID 欄位的 DEFAULT
            cur.execute(f"""
                ALTER TABLE {table_ref} 
                ALTER COLUMN {id_column} SET DEFAULT nextval('{sequence_name}');
            """)
            
            # 將序列的所有權給表
            cur.execute(f"""
                ALTER SEQUENCE {sequence_name} OWNED BY {table_ref}.{id_column};
            """)
            
            conn.commit()
            print(f"✅ {table_name}.{id_column}: 序列已建立，起始值為 {start_value}")
        else:
            # 檢查 DEFAULT 是否正確設定
            cur.execute(f"""
                SELECT column_default
                FROM information_schema.columns
                WHERE table_name = '{table_name.lower()}' AND column_name = '{id_column}';
            """)
            result = cur.fetchone()
            
            if result and result[0] and 'nextval' in str(result[0]):
                print(f"✅ {table_name}.{id_column}: 序列已正確設定")
            else:
                # 設定 DEFAULT
                table_ref = f'"{table_name}"' if use_quotes else table_name
                cur.execute(f"""
                    ALTER TABLE {table_ref} 
                    ALTER COLUMN {id_column} SET DEFAULT nextval('{sequence_name}');
                """)
                conn.commit()
                print(f"✅ {table_name}.{id_column}: DEFAULT 已設定")
        
        cur.close()
    except Exception as e:
        conn.rollback()
        print(f"❌ {table_name}.{id_column}: 錯誤 - {e}")
    finally:
        conn.close()

def fix_all_sequences():
    """修復所有需要的序列"""
    print("開始修復所有表的 ID 序列...\n")
    
    # 需要修復的表和對應的序列名稱
    # 注意：USER 表名需要引號，其他表名是小寫不需要引號
    tables_to_fix = [
        ('clinic_session', 'session_id', 'clinic_session_session_id_seq', False),
        ('appointment', 'appt_id', 'appointment_appt_id_seq', False),
        ('encounter', 'enct_id', 'encounter_enct_id_seq', False),
        ('lab_result', 'lab_id', 'lab_result_lab_id_seq', False),
        ('payment', 'payment_id', 'payment_payment_id_seq', False),
    ]
    
    for table_name, id_column, sequence_name, use_quotes in tables_to_fix:
        fix_sequence(table_name, id_column, sequence_name, use_quotes)
    
    print("\n所有序列修復完成！")

if __name__ == "__main__":
    fix_all_sequences()

