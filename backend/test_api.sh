#!/bin/bash
# API 測試腳本 (使用 curl)
# 請先確保伺服器正在運行：uvicorn app.main:app --port 8000

BASE_URL="http://localhost:8000"

# 測試用的 ID（請根據實際資料庫內容修改）
PROVIDER_ID=1
SESSION_ID=1
APPT_ID=1
ENCT_ID=1
CODE_ICD="A00.0"

echo "============================================================"
echo "開始測試 Clinic Digital System API"
echo "============================================================"
echo "API 基礎 URL: $BASE_URL"
echo ""

# 1. 根路徑測試
echo "測試 1: 根路徑"
curl -s -X GET "$BASE_URL/" | jq .
echo ""

# 2. 取得醫師資料
echo "測試 2: 取得醫師資料"
curl -s -X GET "$BASE_URL/provider/$PROVIDER_ID/profile" | jq .
echo ""

# 3. 列出診次
echo "測試 3: 列出診次（全部）"
curl -s -X GET "$BASE_URL/provider/$PROVIDER_ID/sessions" | jq .
echo ""

echo "測試 4: 列出診次（帶日期篩選）"
curl -s -X GET "$BASE_URL/provider/$PROVIDER_ID/sessions?from_date=2024-01-01&to_date=2024-12-31" | jq .
echo ""

# 4. 列出預約
echo "測試 5: 列出預約"
curl -s -X GET "$BASE_URL/provider/$PROVIDER_ID/sessions/$SESSION_ID/appointments" | jq .
echo ""

# 5. 取得就診記錄
echo "測試 6: 取得就診記錄"
curl -s -X GET "$BASE_URL/provider/$PROVIDER_ID/appointments/$APPT_ID/encounter" | jq .
echo ""

# 6. 建立/更新就診記錄
echo "測試 7: 建立/更新就診記錄"
curl -s -X PUT "$BASE_URL/provider/$PROVIDER_ID/appointments/$APPT_ID/encounter" \
  -H "Content-Type: application/json" \
  -d '{
    "status": 1,
    "chief_complaint": "頭痛",
    "subjective": "患者主訴頭痛已持續三天",
    "assessment": "初步診斷為偏頭痛",
    "plan": "開立止痛藥，建議休息"
  }' | jq .
echo ""

# 7. 取得診斷列表
echo "測試 8: 取得診斷列表"
curl -s -X GET "$BASE_URL/provider/$PROVIDER_ID/encounters/$ENCT_ID/diagnoses" | jq .
echo ""

# 8. 建立/更新診斷
echo "測試 9: 建立/更新診斷"
curl -s -X PUT "$BASE_URL/provider/$PROVIDER_ID/encounters/$ENCT_ID/diagnoses/$CODE_ICD" \
  -H "Content-Type: application/json" \
  -d '{
    "is_primary": false
  }' | jq .
echo ""

# 9. 設定主要診斷
echo "測試 10: 設定主要診斷"
curl -s -X POST "$BASE_URL/provider/$PROVIDER_ID/encounters/$ENCT_ID/primary-diagnosis" \
  -H "Content-Type: application/json" \
  -d "{
    \"code_icd\": \"$CODE_ICD\"
  }" | jq .
echo ""

# 10. 取得處方
echo "測試 11: 取得處方"
curl -s -X GET "$BASE_URL/provider/$PROVIDER_ID/encounters/$ENCT_ID/prescription" | jq .
echo ""

# 11. 建立/更新處方
echo "測試 12: 建立/更新處方"
curl -s -X PUT "$BASE_URL/provider/$PROVIDER_ID/encounters/$ENCT_ID/prescription" \
  -H "Content-Type: application/json" \
  -d '{
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
  }' | jq .
echo ""

echo "============================================================"
echo "測試完成"
echo "============================================================"


