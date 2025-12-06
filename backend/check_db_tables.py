#!/usr/bin/env python3
"""
檢查資料庫連線並顯示每個表的前三列和後三列
"""
import psycopg2
from app.config import PG_DSN

def get_table_names(conn):
    """取得所有表名"""
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cur.fetchall()]
    cur.close()
    return tables

def get_table_columns(conn, table_name):
    """取得表的所有欄位名稱"""
    cur = conn.cursor()
    # 處理大小寫敏感的表名
    if table_name.isupper():
        quoted_table = f'"{table_name}"'
    else:
        quoted_table = table_name
    
    try:
        cur.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name.lower()}' 
            OR table_name = '{table_name}'
            ORDER BY ordinal_position;
        """)
        columns = [row[0] for row in cur.fetchall()]
        cur.close()
        return columns
    except Exception as e:
        print(f"  錯誤：無法取得 {table_name} 的欄位資訊: {e}")
        cur.close()
        return []

def get_table_data(conn, table_name, limit=3):
    """取得表的前 N 列和後 N 列"""
    cur = conn.cursor()
    
    # 處理大小寫敏感的表名
    if table_name.isupper():
        quoted_table = f'"{table_name}"'
    else:
        quoted_table = table_name
    
    try:
        # 取得總行數
        cur.execute(f'SELECT COUNT(*) FROM {quoted_table};')
        total_count = cur.fetchone()[0]
        
        if total_count == 0:
            return [], []
        
        # 取得前 N 列
        cur.execute(f'SELECT * FROM {quoted_table} LIMIT {limit};')
        first_rows = cur.fetchall()
        
        # 取得後 N 列
        if total_count > limit:
            offset = max(0, total_count - limit)
            cur.execute(f'SELECT * FROM {quoted_table} OFFSET {offset} LIMIT {limit};')
            last_rows = cur.fetchall()
        else:
            last_rows = []
        
        cur.close()
        return first_rows, last_rows, total_count
    except Exception as e:
        print(f"  錯誤：無法查詢 {table_name}: {e}")
        cur.close()
        return [], [], 0

def format_row(row, columns):
    """格式化行資料"""
    if not row:
        return "無資料"
    result = []
    for i, col in enumerate(columns):
        if i < len(row):
            value = row[i]
            if value is None:
                value = "NULL"
            elif isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            result.append(f"{col}={value}")
    return " | ".join(result)

def main():
    print("=" * 80)
    print("資料庫連線檢查")
    print("=" * 80)
    
    try:
        # 測試連線
        print("\n正在連線到資料庫...")
        conn = psycopg2.connect(PG_DSN)
        print(f"✅ 連線成功！")
        print(f"   資料庫: {PG_DSN.split('dbname=')[1].split()[0]}")
        
        # 取得所有表
        print("\n正在取得表列表...")
        tables = get_table_names(conn)
        
        if not tables:
            print("⚠️  資料庫中沒有任何表")
            conn.close()
            return
        
        print(f"✅ 找到 {len(tables)} 個表：")
        for table in tables:
            print(f"   - {table}")
        
        # 對每個表顯示資料
        print("\n" + "=" * 80)
        print("表資料預覽（前 3 列和後 3 列）")
        print("=" * 80)
        
        for table_name in tables:
            print(f"\n📊 表: {table_name}")
            print("-" * 80)
            
            # 取得欄位資訊
            columns = get_table_columns(conn, table_name)
            if not columns:
                print("  ⚠️  無法取得欄位資訊")
                continue
            
            print(f"  欄位: {', '.join(columns)}")
            
            # 取得資料
            first_rows, last_rows, total_count = get_table_data(conn, table_name, limit=3)
            
            print(f"  總行數: {total_count}")
            
            if total_count == 0:
                print("  ⚠️  表為空")
                continue
            
            # 顯示前三列
            if first_rows:
                print(f"\n  【前 3 列】")
                for i, row in enumerate(first_rows, 1):
                    print(f"    {i}. {format_row(row, columns)}")
            
            # 顯示後三列
            if last_rows and len(last_rows) > 0 and (total_count > 3 or first_rows != last_rows):
                print(f"\n  【後 3 列】")
                start_num = max(1, total_count - len(last_rows) + 1)
                for i, row in enumerate(last_rows, start_num):
                    print(f"    {i}. {format_row(row, columns)}")
        
        conn.close()
        print("\n" + "=" * 80)
        print("✅ 檢查完成")
        print("=" * 80)
        
    except psycopg2.OperationalError as e:
        print(f"❌ 連線失敗: {e}")
        print("\n請檢查：")
        print("  1. PostgreSQL 服務是否正在運行")
        print("  2. 資料庫名稱、用戶名、密碼是否正確")
        print("  3. .env 檔案中的設定是否正確")
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

