#!/usr/bin/env python3
"""
調試註冊功能的腳本
用於檢查實際的錯誤詳情
"""
import sys
import traceback
from app.services.provider_service import ProviderService
from app.services.patient_service import PatientService
import psycopg2

def test_provider_register(name, password, license_no, dept_id):
    """測試醫師註冊"""
    print(f"\n=== 測試醫師註冊 ===")
    print(f"姓名: {name}")
    print(f"執照號碼: {license_no}")
    print(f"科別 ID: {dept_id}")
    
    service = ProviderService()
    try:
        result = service.register_provider(name, password, license_no, dept_id)
        print(f"✅ 註冊成功！")
        print(f"結果: {result}")
        return True
    except Exception as e:
        print(f"❌ 註冊失敗")
        print(f"錯誤類型: {type(e).__name__}")
        print(f"錯誤訊息: {str(e)}")
        
        # 如果是 IntegrityError，顯示詳細資訊
        if isinstance(e, psycopg2.IntegrityError):
            print(f"PostgreSQL 錯誤代碼: {e.pgcode}")
            print(f"錯誤詳情: {e.pgerror}")
            print(f"完整錯誤: {repr(e)}")
        
        # 顯示完整的 traceback
        print("\n完整錯誤堆疊:")
        traceback.print_exc()
        return False

def test_patient_register(name, password, national_id, birth_date, sex, phone):
    """測試病人註冊"""
    print(f"\n=== 測試病人註冊 ===")
    print(f"姓名: {name}")
    print(f"身分證字號: {national_id}")
    print(f"生日: {birth_date}")
    
    service = PatientService()
    try:
        result = service.register_patient(name, password, national_id, birth_date, sex, phone)
        print(f"✅ 註冊成功！")
        print(f"結果: {result}")
        return True
    except Exception as e:
        print(f"❌ 註冊失敗")
        print(f"錯誤類型: {type(e).__name__}")
        print(f"錯誤訊息: {str(e)}")
        
        # 如果是 IntegrityError，顯示詳細資訊
        if isinstance(e, psycopg2.IntegrityError):
            print(f"PostgreSQL 錯誤代碼: {e.pgcode}")
            print(f"錯誤詳情: {e.pgerror}")
            print(f"完整錯誤: {repr(e)}")
        
        # 顯示完整的 traceback
        print("\n完整錯誤堆疊:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  測試醫師註冊: python debug_register.py provider <name> <password> <license_no> <dept_id>")
        print("  測試病人註冊: python debug_register.py patient <name> <password> <national_id> <birth_date> <sex> <phone>")
        print("\n範例:")
        print("  python debug_register.py provider '張醫師' 'pass123' 'DOC001' 1")
        print("  python debug_register.py patient '王病人' 'pass123' 'A123456789' '2000-01-01' 'M' '0912345678'")
        sys.exit(1)
    
    if sys.argv[1] == "provider":
        if len(sys.argv) != 6:
            print("錯誤：醫師註冊需要 4 個參數：name, password, license_no, dept_id")
            sys.exit(1)
        test_provider_register(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]))
    elif sys.argv[1] == "patient":
        if len(sys.argv) != 8:
            print("錯誤：病人註冊需要 6 個參數：name, password, national_id, birth_date, sex, phone")
            sys.exit(1)
        test_patient_register(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])
    else:
        print(f"錯誤：未知的類型 '{sys.argv[1]}'，請使用 'provider' 或 'patient'")
        sys.exit(1)

