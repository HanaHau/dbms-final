#!/usr/bin/env python3
"""
將 DISEASE 表的 desc 欄位重命名為 description
"""
import psycopg2
from app.config import PG_DSN

def rename_disease_desc_column():
    """將 DISEASE 表的 desc 欄位重命名為 description"""
    conn = psycopg2.connect(PG_DSN)
    try:
        cur = conn.cursor()
        
        # 檢查 desc 欄位是否存在
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'disease' 
            AND column_name = 'desc';
        """)
        
        if cur.fetchone():
            # 檢查 description 欄位是否已存在
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'disease' 
                AND column_name = 'description';
            """)
            
            if cur.fetchone():
                print("⚠️  description 欄位已存在，無法重命名")
                print("   如果需要，請先刪除 description 欄位或手動處理")
            else:
                # 重命名欄位（desc 是保留字，需要用引號）
                cur.execute("""
                    ALTER TABLE DISEASE 
                    RENAME COLUMN "desc" TO description;
                """)
                conn.commit()
                print("✅ 已將 DISEASE.desc 重命名為 DISEASE.description")
        else:
            # 檢查 description 欄位是否存在
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'disease' 
                AND column_name = 'description';
            """)
            
            if cur.fetchone():
                print("✅ DISEASE.description 欄位已存在，無需重命名")
            else:
                print("⚠️  找不到 DISEASE.desc 欄位，也找不到 DISEASE.description 欄位")
                print("   請檢查資料庫結構")
        
        cur.close()
    except Exception as e:
        conn.rollback()
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("將 DISEASE 表的 desc 欄位重命名為 description")
    print("=" * 60)
    print()
    
    try:
        rename_disease_desc_column()
        print("\n✓ 腳本執行成功")
    except Exception as e:
        print(f"\n✗ 腳本執行失敗: {str(e)}")
        exit(1)

