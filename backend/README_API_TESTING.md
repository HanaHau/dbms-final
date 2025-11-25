# API 測試指南

本文件說明如何測試 Clinic Digital System API 的所有端點。

## 快速開始

### 方法 1: 使用 FastAPI 自動生成的 API 文檔（推薦）

FastAPI 自動提供了互動式 API 文檔，這是最簡單的測試方式：

1. **啟動伺服器**：
   ```bash
   cd backend
   uvicorn app.main:app --port 8001
   ```

2. **打開瀏覽器訪問**：
   - Swagger UI（互動式文檔）: http://localhost:8001/docs
   - ReDoc（替代文檔）: http://localhost:8001/redoc

3. **在 Swagger UI 中測試**：
   - 點擊任何端點展開詳細資訊
   - 點擊 "Try it out" 按鈕
   - 填入參數
   - 點擊 "Execute" 執行請求
   - 查看回應結果

### 方法 2: 使用 Python 測試腳本

1. **確保已安裝 requests**：
   ```bash
   pip install requests
   ```

2. **修改測試腳本中的測試 ID**：
   編輯 `test_api.py`，根據你的資料庫內容修改以下變數：
   ```python
   TEST_PROVIDER_ID = 1      # 實際的醫師 ID
   TEST_SESSION_ID = 1       # 實際的診次 ID
   TEST_APPT_ID = 1          # 實際的預約 ID
   TEST_ENCT_ID = 1          # 實際的就診記錄 ID
   TEST_CODE_ICD = "A00.0"   # 實際的 ICD 代碼
   ```

3. **執行測試**：
   ```bash
   cd backend
   python test_api.py
   ```

### 方法 3: 使用 curl 命令

1. **確保已安裝 jq**（用於格式化 JSON 輸出）：
   ```bash
   # macOS
   brew install jq
   
   # Linux
   sudo apt-get install jq
   ```

2. **修改測試腳本中的測試 ID**：
   編輯 `test_api.sh`，修改以下變數：
   ```bash
   PROVIDER_ID=1
   SESSION_ID=1
   APPT_ID=1
   ENCT_ID=1
   CODE_ICD="A00.0"
   ```

3. **執行測試**：
   ```bash
   cd backend
   chmod +x test_api.sh
   ./test_api.sh
   ```

## API 端點列表

所有 Provider API 都掛載在 `/provider` 前綴下：

### 1. 取得醫師資料
- **GET** `/provider/{provider_id}/profile`
- 取得指定醫師的基本資料

### 2. 列出診次
- **GET** `/provider/{provider_id}/sessions`
- 查詢參數：
  - `from_date` (可選): 開始日期 (YYYY-MM-DD)
  - `to_date` (可選): 結束日期 (YYYY-MM-DD)
  - `status` (可選): 狀態碼

### 3. 列出預約
- **GET** `/provider/{provider_id}/sessions/{session_id}/appointments`
- 取得指定診次的所有預約

### 4. 取得就診記錄
- **GET** `/provider/{provider_id}/appointments/{appt_id}/encounter`
- 取得指定預約的就診記錄

### 5. 建立/更新就診記錄
- **PUT** `/provider/{provider_id}/appointments/{appt_id}/encounter`
- 請求體：
  ```json
  {
    "status": 1,
    "chief_complaint": "主訴",
    "subjective": "主觀描述",
    "assessment": "評估",
    "plan": "計畫"
  }
  ```

### 6. 取得診斷列表
- **GET** `/provider/{provider_id}/encounters/{enct_id}/diagnoses`
- 取得指定就診記錄的所有診斷

### 7. 建立/更新診斷
- **PUT** `/provider/{provider_id}/encounters/{enct_id}/diagnoses/{code_icd}`
- 請求體：
  ```json
  {
    "is_primary": false
  }
  ```

### 8. 設定主要診斷
- **POST** `/provider/{provider_id}/encounters/{enct_id}/primary-diagnosis`
- 請求體：
  ```json
  {
    "code_icd": "A00.0"
  }
  ```

### 9. 取得處方
- **GET** `/provider/{provider_id}/encounters/{enct_id}/prescription`
- 取得指定就診記錄的處方

### 10. 建立/更新處方
- **PUT** `/provider/{provider_id}/encounters/{enct_id}/prescription`
- 請求體：
  ```json
  {
    "status": 1,
    "items": [
      {
        "med_id": 1,
        "dosage": "500mg",
        "frequency": "一天三次",
        "days": 7,
        "quantity": 21.0
      }
    ]
  }
  ```

## 手動測試範例（curl）

### 取得醫師資料
```bash
curl -X GET "http://localhost:8001/provider/1/profile"
```

### 列出診次（帶日期篩選）
```bash
curl -X GET "http://localhost:8001/provider/1/sessions?from_date=2024-01-01&to_date=2024-12-31"
```

### 建立/更新就診記錄
```bash
curl -X PUT "http://localhost:8001/provider/1/appointments/1/encounter" \
  -H "Content-Type: application/json" \
  -d '{
    "status": 1,
    "chief_complaint": "頭痛",
    "subjective": "患者主訴頭痛已持續三天",
    "assessment": "初步診斷為偏頭痛",
    "plan": "開立止痛藥，建議休息"
  }'
```

### 建立/更新處方
```bash
curl -X PUT "http://localhost:8001/provider/1/encounters/1/prescription" \
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
      }
    ]
  }'
```

## 注意事項

1. **測試前準備**：
   - 確保 PostgreSQL 資料庫已啟動並包含測試資料
   - 確保 `.env` 檔案中的資料庫連線設定正確
   - 確保伺服器正在運行

2. **測試 ID**：
   - 所有測試腳本中的 ID 都是範例值
   - 請根據實際資料庫內容修改這些 ID

3. **錯誤處理**：
   - 404 錯誤表示資源不存在（可能是 ID 錯誤或資料庫中沒有該筆資料）
   - 500 錯誤表示伺服器內部錯誤（檢查伺服器日誌）

4. **資料庫狀態**：
   - 某些測試（如建立/更新）會修改資料庫
   - 建議在測試環境中執行，或使用測試資料

## 疑難排解

### 無法連接到伺服器
- 確認伺服器是否正在運行：`ps aux | grep uvicorn`
- 確認端口是否正確（預設為 8001）

### 資料庫連線錯誤
- 檢查 `.env` 檔案中的資料庫設定
- 確認 PostgreSQL 服務是否運行
- 確認資料庫名稱、使用者名稱、密碼是否正確

### 404 錯誤
- 確認 URL 路徑是否正確
- 確認 ID 是否存在於資料庫中
- 檢查路由前綴是否正確（`/provider`）

