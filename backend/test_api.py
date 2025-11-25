#!/usr/bin/env python3
"""
API 測試腳本
測試所有 Provider API 端點

使用方法：
1. 確保伺服器正在運行：uvicorn app.main:app --port 8001
2. 執行此腳本：python test_api.py
"""

import requests
import json
from datetime import date, datetime

# API 基礎 URL
BASE_URL = "http://localhost:8001"

# 測試用的 ID（請根據實際資料庫內容修改）
TEST_PROVIDER_ID = 1
TEST_SESSION_ID = 1
TEST_APPT_ID = 1
TEST_ENCT_ID = 1
TEST_CODE_ICD = "A00.0"  # 範例 ICD 代碼


def print_response(title, response):
    """格式化輸出回應結果"""
    print(f"\n{'='*60}")
    print(f"測試: {title}")
    print(f"{'='*60}")
    print(f"URL: {response.url}")
    print(f"狀態碼: {response.status_code}")
    try:
        print(f"回應內容:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(f"回應內容: {response.text}")
    print()


def test_root():
    """測試根路徑"""
    response = requests.get(f"{BASE_URL}/")
    print_response("根路徑測試", response)
    return response.status_code == 200


def test_get_provider_profile(provider_id):
    """測試取得醫師資料"""
    response = requests.get(f"{BASE_URL}/provider/{provider_id}/profile")
    print_response(f"取得醫師資料 (provider_id={provider_id})", response)
    return response.status_code in [200, 404]


def test_list_sessions(provider_id, from_date=None, to_date=None, status=None):
    """測試列出診次"""
    params = {}
    if from_date:
        params["from_date"] = from_date
    if to_date:
        params["to_date"] = to_date
    if status is not None:
        params["status"] = status
    
    response = requests.get(
        f"{BASE_URL}/provider/{provider_id}/sessions",
        params=params
    )
    print_response(
        f"列出診次 (provider_id={provider_id}, params={params})",
        response
    )
    return response.status_code == 200


def test_list_appointments(provider_id, session_id):
    """測試列出預約"""
    response = requests.get(
        f"{BASE_URL}/provider/{provider_id}/sessions/{session_id}/appointments"
    )
    print_response(
        f"列出預約 (provider_id={provider_id}, session_id={session_id})",
        response
    )
    return response.status_code == 200


def test_get_encounter(provider_id, appt_id):
    """測試取得就診記錄"""
    response = requests.get(
        f"{BASE_URL}/provider/{provider_id}/appointments/{appt_id}/encounter"
    )
    print_response(
        f"取得就診記錄 (provider_id={provider_id}, appt_id={appt_id})",
        response
    )
    return response.status_code in [200, 404]


def test_upsert_encounter(provider_id, appt_id):
    """測試建立/更新就診記錄"""
    data = {
        "status": 1,
        "chief_complaint": "頭痛",
        "subjective": "患者主訴頭痛已持續三天",
        "assessment": "初步診斷為偏頭痛",
        "plan": "開立止痛藥，建議休息"
    }
    response = requests.put(
        f"{BASE_URL}/provider/{provider_id}/appointments/{appt_id}/encounter",
        json=data
    )
    print_response(
        f"建立/更新就診記錄 (provider_id={provider_id}, appt_id={appt_id})",
        response
    )
    return response.status_code == 200


def test_get_diagnoses(provider_id, enct_id):
    """測試取得診斷列表"""
    response = requests.get(
        f"{BASE_URL}/provider/{provider_id}/encounters/{enct_id}/diagnoses"
    )
    print_response(
        f"取得診斷列表 (provider_id={provider_id}, enct_id={enct_id})",
        response
    )
    return response.status_code == 200


def test_upsert_diagnosis(provider_id, enct_id, code_icd, is_primary=False):
    """測試建立/更新診斷"""
    data = {
        "is_primary": is_primary
    }
    response = requests.put(
        f"{BASE_URL}/provider/{provider_id}/encounters/{enct_id}/diagnoses/{code_icd}",
        json=data
    )
    print_response(
        f"建立/更新診斷 (provider_id={provider_id}, enct_id={enct_id}, code_icd={code_icd})",
        response
    )
    return response.status_code == 200


def test_set_primary_diagnosis(provider_id, enct_id, code_icd):
    """測試設定主要診斷"""
    data = {
        "code_icd": code_icd
    }
    response = requests.post(
        f"{BASE_URL}/provider/{provider_id}/encounters/{enct_id}/primary-diagnosis",
        json=data
    )
    print_response(
        f"設定主要診斷 (provider_id={provider_id}, enct_id={enct_id}, code_icd={code_icd})",
        response
    )
    return response.status_code == 200


def test_get_prescription(provider_id, enct_id):
    """測試取得處方"""
    response = requests.get(
        f"{BASE_URL}/provider/{provider_id}/encounters/{enct_id}/prescription"
    )
    print_response(
        f"取得處方 (provider_id={provider_id}, enct_id={enct_id})",
        response
    )
    return response.status_code in [200, 404]


def test_upsert_prescription(provider_id, enct_id):
    """測試建立/更新處方"""
    data = {
        "status": 1,
        "items": [
            {
                "med_id": 1,
                "dosage": "500mg",
                "frequency": "一天三次",
                "days": 7,
                "quantity": 21.0
            },
            {
                "med_id": 2,
                "dosage": "10mg",
                "frequency": "一天一次",
                "days": 5,
                "quantity": 5.0
            }
        ]
    }
    response = requests.put(
        f"{BASE_URL}/provider/{provider_id}/encounters/{enct_id}/prescription",
        json=data
    )
    print_response(
        f"建立/更新處方 (provider_id={provider_id}, enct_id={enct_id})",
        response
    )
    return response.status_code == 200


def main():
    """執行所有測試"""
    print("="*60)
    print("開始測試 Clinic Digital System API")
    print("="*60)
    print(f"API 基礎 URL: {BASE_URL}")
    print(f"測試用的 ID: provider_id={TEST_PROVIDER_ID}, session_id={TEST_SESSION_ID}")
    print(f"              appt_id={TEST_APPT_ID}, enct_id={TEST_ENCT_ID}")
    print("="*60)
    
    results = []
    
    # 1. 根路徑測試
    results.append(("根路徑", test_root()))
    
    # 2. Provider API 測試
    print("\n" + "="*60)
    print("Provider API 測試")
    print("="*60)
    
    results.append(("取得醫師資料", test_get_provider_profile(TEST_PROVIDER_ID)))
    
    results.append(("列出診次（全部）", test_list_sessions(TEST_PROVIDER_ID)))
    results.append(("列出診次（帶日期）", test_list_sessions(
        TEST_PROVIDER_ID,
        from_date="2024-01-01",
        to_date="2024-12-31"
    )))
    
    results.append(("列出預約", test_list_appointments(TEST_PROVIDER_ID, TEST_SESSION_ID)))
    
    results.append(("取得就診記錄", test_get_encounter(TEST_PROVIDER_ID, TEST_APPT_ID)))
    
    results.append(("建立/更新就診記錄", test_upsert_encounter(TEST_PROVIDER_ID, TEST_APPT_ID)))
    
    results.append(("取得診斷列表", test_get_diagnoses(TEST_PROVIDER_ID, TEST_ENCT_ID)))
    
    results.append(("建立/更新診斷", test_upsert_diagnosis(
        TEST_PROVIDER_ID, TEST_ENCT_ID, TEST_CODE_ICD, is_primary=False
    )))
    
    results.append(("設定主要診斷", test_set_primary_diagnosis(
        TEST_PROVIDER_ID, TEST_ENCT_ID, TEST_CODE_ICD
    )))
    
    results.append(("取得處方", test_get_prescription(TEST_PROVIDER_ID, TEST_ENCT_ID)))
    
    results.append(("建立/更新處方", test_upsert_prescription(TEST_PROVIDER_ID, TEST_ENCT_ID)))
    
    # 輸出測試結果摘要
    print("\n" + "="*60)
    print("測試結果摘要")
    print("="*60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    for test_name, result in results:
        status = "✓ 通過" if result else "✗ 失敗"
        print(f"{status}: {test_name}")
    print(f"\n總計: {passed}/{total} 測試通過")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n錯誤: 無法連接到伺服器！")
        print("請確保伺服器正在運行：")
        print("  uvicorn app.main:app --port 8001")
    except Exception as e:
        print(f"\n發生錯誤: {e}")
        import traceback
        traceback.print_exc()

