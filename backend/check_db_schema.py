#!/usr/bin/env python3
"""
檢查資料庫結構的腳本
"""
import psycopg2
from app.config import PG_DSN

try:
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()
    
    print("=== 檢查 USER 表的結構 ===")
    cur.execute("""
        SELECT column_name, data_type, column_default, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'USER'
        ORDER BY ordinal_position;
    """)
    columns = cur.fetchall()
    for col in columns:
        print(f"  {col[0]}: {col[1]} | Default: {col[2]} | Nullable: {col[3]}")
    
    print("\n=== 檢查 USER 表的序列 ===")
    cur.execute("""
        SELECT column_name, column_default
        FROM information_schema.columns
        WHERE table_name = 'USER' AND column_name = 'user_id';
    """)
    seq_info = cur.fetchone()
    if seq_info:
        print(f"  user_id 的 DEFAULT: {seq_info[1]}")
    
    print("\n=== 檢查序列是否存在 ===")
    cur.execute("""
        SELECT sequence_name 
        FROM information_schema.sequences 
        WHERE sequence_schema = 'public' 
        AND sequence_name LIKE '%user%';
    """)
    sequences = cur.fetchall()
    for seq in sequences:
        print(f"  找到序列: {seq[0]}")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"錯誤: {e}")
    import traceback
    traceback.print_exc()

