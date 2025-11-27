#!/usr/bin/env python3
"""
檢查實際的表名
"""
import psycopg2
from app.config import PG_DSN

conn = psycopg2.connect(PG_DSN)
cur = conn.cursor()

# 查詢所有表名
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name;
""")

tables = cur.fetchall()
print("資料庫中的所有表：")
for table in tables:
    print(f"  {table[0]}")

cur.close()
conn.close()

