# Clinic Digital System API

一個基於 FastAPI 的診所數位化系統後端 API，提供醫師端（Provider）和病人端（Patient）的完整功能，包括帳號管理、門診時段管理、掛號管理、就診記錄、診斷與處方管理、歷史記錄查詢、資料分析等。

## 📋 專案簡介

本專案是一個診所管理系統的後端 API，實作了醫師端和病人端的完整功能。系統使用 PostgreSQL 作為主要資料庫，並整合 DuckDB 進行資料分析。所有 API 遵循 RESTful 設計原則，並提供完整的 Swagger 文檔。

## 🛠 技術棧

- **後端框架**: FastAPI
- **資料庫**: PostgreSQL (主要資料庫)
- **分析資料庫**: DuckDB (用於資料分析)
- **Python 版本**: 3.12+
- **主要依賴**:
  - `fastapi` - Web 框架
  - `uvicorn` - ASGI 伺服器
  - `psycopg2-binary` - PostgreSQL 驅動
  - `duckdb` - 分析型資料庫
  - `python-dotenv` - 環境變數管理

## 📁 專案結構

```
dbms-final/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI 應用程式入口
│   │   ├── config.py                  # 配置管理（資料庫連線設定）
│   │   ├── pg_basep.py                 # PostgreSQL 基礎功能（連線、ID 生成）
│   │   ├── pg_provider.py             # Provider 相關的資料庫操作函數
│   │   ├── router_provider.py         # Provider API 路由定義
│   │   ├── db_duck.py                 # DuckDB 分析功能
│   │   ├── repositories/              # 資料庫操作層（Repository Pattern）
│   │   │   ├── __init__.py
│   │   │   ├── provider_repo.py
│   │   │   ├── session_repo.py
│   │   │   ├── appointment_repo.py
│   │   │   ├── encounter_repo.py
│   │   │   ├── diagnosis_repo.py
│   │   │   ├── prescription_repo.py
│   │   │   ├── lab_result_repo.py
│   │   │   └── payment_repo.py
│   │   ├── services/                  # 業務邏輯層（Service Layer）
│   │   │   ├── __init__.py
│   │   │   ├── provider_service.py
│   │   │   ├── patient_history_service.py
│   │   │   └── shared/
│   │   │       ├── __init__.py
│   │   │       ├── session_service.py
│   │   │       └── appointment_service.py
│   │   ├── routers/                   # API 路由層
│   │   │   ├── __init__.py
│   │   │   └── patient_router.py
│   │   └── analytics/                 # 資料分析功能
│   │       ├── __init__.py
│   │       └── patient_analysis.py
│   ├── requirements.txt                # Python 依賴套件
│   ├── test_api.py                     # Python API 測試腳本
│   └── test_api.sh                     # Shell API 測試腳本
└── README.md
```

## ✨ 已實作功能

### 1. 病人端（Patient）帳號管理
- ✅ 病人註冊 (`POST /patient/register`)
- ✅ 病人登入 (`POST /patient/login`)
- ✅ 取得病人資料 (`GET /patient/{patient_id}/profile`)

### 2. 醫師端（Provider）帳號管理
- ✅ 醫師註冊 (`POST /provider/register`)
- ✅ 醫師登入 (`POST /provider/login`)
- ✅ 取得醫師資料 (`GET /provider/{provider_id}/profile`)

### 3. 門診時段管理
- ✅ 列出診次 (`GET /provider/{provider_id}/sessions`)
  - 支援日期範圍篩選
  - 支援狀態篩選
- ✅ 建立診次 (`POST /provider/{provider_id}/sessions`)
- ✅ 更新診次 (`PUT /provider/{provider_id}/sessions/{session_id}`)
- ✅ 取消診次 (`POST /provider/{provider_id}/sessions/{session_id}/cancel`)

### 4. 預約管理（醫師端）
- ✅ 列出預約 (`GET /provider/{provider_id}/sessions/{session_id}/appointments`)

### 5. 預約管理（病人端）
- ✅ 查詢可預約門診時段 (`GET /patient/sessions`)
  - 支援科別、醫師、日期篩選
- ✅ 列出所有掛號 (`GET /patient/appointments`)
- ✅ 建立掛號 (`POST /patient/appointments`)
  - ✅ 檢查是否已在該 session 重複掛號
  - ✅ 檢查 session 容量是否已滿
  - ✅ 使用 transaction + FOR UPDATE 避免併行衝突
  - ✅ 自動計算 slot_seq
  - ✅ 寫入掛號狀態歷史
- ✅ 取消掛號 (`DELETE /patient/appointments/{id}`)
  - ✅ 驗證 patient_id 是否匹配
  - ✅ 更新狀態為「已取消」
  - ✅ 寫入狀態歷史
- ✅ 修改掛號（改期）(`PATCH /patient/appointments/{id}/reschedule`)
  - ✅ 使用固定鎖序避免死鎖
  - ✅ 更新 session_id 和 slot_seq
  - ✅ 寫入狀態歷史
- ✅ 病人報到 (`POST /patient/appointments/{id}/checkin`)
  - ✅ 驗證 patient_id 是否匹配
  - ✅ 更新狀態為「已報到」
  - ✅ 寫入狀態歷史

### 6. 就診記錄（Encounter）
- ✅ 取得就診記錄 (`GET /provider/{provider_id}/appointments/{appt_id}/encounter`)
- ✅ 建立/更新就診記錄 (`PUT /provider/{provider_id}/appointments/{appt_id}/encounter`)
  - 包含主訴、主觀描述、評估、計畫等欄位
  - ✅ 支援草稿與定稿狀態
  - ✅ 已定稿的就診記錄不可再編輯

### 7. 診斷管理
- ✅ 取得診斷列表 (`GET /provider/{provider_id}/encounters/{enct_id}/diagnoses`)
- ✅ 建立/更新診斷 (`PUT /provider/{provider_id}/encounters/{enct_id}/diagnoses/{code_icd}`)
- ✅ 設定主要診斷 (`POST /provider/{provider_id}/encounters/{enct_id}/primary-diagnosis`)
  - ✅ 使用 transaction 確保原子性
  - ✅ 驗證診斷是否存在

### 8. 處方管理
- ✅ 取得處方 (`GET /provider/{provider_id}/encounters/{enct_id}/prescription`)
- ✅ 建立/更新處方 (`PUT /provider/{provider_id}/encounters/{enct_id}/prescription`)
  - 支援多個藥品項目
  - 每個項目包含劑量、頻率、天數、數量等資訊
  - ✅ 使用 transaction 確保原子性

### 9. 檢驗報告管理
- ✅ 取得檢驗結果列表 (`GET /provider/{provider_id}/encounters/{enct_id}/lab-results`)
- ✅ 新增檢驗結果 (`POST /provider/{provider_id}/encounters/{enct_id}/lab-results`)
  - 包含 LOINC 代碼、項目名稱、數值、單位、參考範圍、異常標記等

### 10. 繳費管理
- ✅ 取得繳費資訊 (`GET /provider/{provider_id}/encounters/{enct_id}/payment`)
- ✅ 建立/更新繳費資料 (`POST /provider/{provider_id}/encounters/{enct_id}/payment`)
  - 自動產生費用資料
  - 支援多種付款方式

### 11. 病人歷史記錄查詢
- ✅ 查詢完整歷史記錄 (`GET /patient/history`)
  - 所有就診記錄
  - 所有處方箋
  - 所有檢驗結果
  - 所有繳費記錄
- ✅ 列出繳費記錄 (`GET /patient/payments`)

### 12. 線上繳費
- ✅ 線上繳費 (`POST /patient/payments/{payment_id}/pay`)
  - ✅ 驗證 payment 是否屬於該病人
  - ✅ 更新付款方式與發票號碼

### 13. 資料分析
- ✅ DuckDB 整合（用於資料分析查詢）
- ✅ 每日看診統計功能
- ✅ 病人統計分析（年度就診次數、科別分布、常見診斷）

### 14. 病人端功能（Patient）
- ✅ 查詢可預約門診時段 (`GET /patient/sessions`)
- ✅ 列出所有掛號 (`GET /patient/appointments`)
- ✅ 建立掛號 (`POST /patient/appointments`)
  - 使用 transaction + FOR UPDATE 避免併行衝突
  - 自動計算 slot_seq
  - 寫入掛號狀態歷史
- ✅ 取消掛號 (`DELETE /patient/appointments/{id}`)
- ✅ 修改掛號（改期）(`PATCH /patient/appointments/{id}/reschedule`)
  - 使用固定鎖序避免死鎖
- ✅ 病人報到 (`POST /patient/appointments/{id}/checkin`)
- ✅ 查詢完整歷史記錄 (`GET /patient/history`)
  - 所有就診記錄
  - 所有處方箋
  - 所有檢驗結果
  - 所有繳費記錄

## 🚀 安裝與設定

### 1. 環境需求

- Python 3.12 或更高版本
- PostgreSQL 資料庫
- pip（Python 套件管理器）

### 2. 安裝依賴

```bash
cd backend
pip install -r requirements.txt
```

### 3. 資料庫設定

在 `backend` 目錄下建立 `.env` 檔案：

```env
PG_HOST=localhost
PG_PORT=5432
PG_DB=dbms
PG_USER=your_username
PG_PASSWORD=your_password
```

**注意**: 請根據你的 PostgreSQL 設定修改上述值。

### 4. 資料庫準備

確保 PostgreSQL 資料庫已建立，並且包含以下必要的資料表：
- `USER` - 使用者基本資料
- `PROVIDER` - 醫師資料
- `PATIENT` - 病人資料
- `DEPARTMENT` - 科別資料
- `CLINIC_SESSION` - 門診時段
- `APPOINTMENT` - 掛號記錄
- `APPOINTMENT_STATUS_HISTORY` - 掛號狀態歷史
- `ENCOUNTER` - 就診記錄
- `DIAGNOSIS` - 診斷記錄
- `DISEASE` - 疾病資料
- `PRESCRIPTION` - 處方箋
- `INCLUDE` - 處方用藥明細
- `MEDICATION` - 藥品資料
- `LAB_RESULT` - 檢驗結果
- `PAYMENT` - 繳費記錄
- 以及其他相關資料表

## 🏃 執行方式

### 啟動伺服器

```bash
cd backend
uvicorn app.main:app
```

伺服器啟動後，你可以訪問：
- **API 根路徑**: http://localhost:8000/
- **Swagger UI 文檔**: http://localhost:8000/docs
- **ReDoc 文檔**: http://localhost:8000/redoc

**注意**: uvicorn 預設使用端口 8000。

### 指定不同端口

如果預設端口 8000 已被佔用，可以指定其他端口：

```bash
uvicorn app.main:app --port 8001
```

## 🧪 API 測試方法

### 方法 1: 使用 Swagger UI（推薦，最簡單）

1. 啟動伺服器後，打開瀏覽器訪問：http://localhost:8000/docs
2. 在 Swagger UI 中：
   - 點擊任何 API 端點展開詳細資訊
   - 點擊 **"Try it out"** 按鈕
   - 填入必要的參數
   - 點擊 **"Execute"** 執行請求
   - 查看回應結果

這是測試 API 最直觀的方式，無需額外工具。

### 方法 2: 使用 Python 測試腳本

1. **安裝 requests**（如果尚未安裝）：
   ```bash
   pip install requests
   ```

2. **修改測試參數**：
   編輯 `backend/test_api.py`，根據你的資料庫內容修改以下變數（第 15-19 行）：
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

測試腳本會執行所有 API 端點並顯示詳細的測試結果。

### 方法 3: 使用 Shell 腳本（curl）

1. **安裝 jq**（用於格式化 JSON 輸出）：
   ```bash
   # macOS
   brew install jq
   
   # Linux (Ubuntu/Debian)
   sudo apt-get install jq
   ```

2. **修改測試參數**：
   編輯 `backend/test_api.sh`，修改以下變數：
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

### 方法 4: 手動使用 curl

以下是一些常用的 curl 測試範例：

#### 測試根路徑
```bash
curl http://localhost:8000/
```

#### 醫師註冊
```bash
curl -X POST "http://localhost:8000/provider/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "張醫師",
    "password": "password123",
    "license_no": "DOC001",
    "dept_id": 1
  }'
```

#### 醫師登入
```bash
curl -X POST "http://localhost:8000/provider/login" \
  -H "Content-Type: application/json" \
  -d '{
    "license_no": "DOC001",
    "password": "password123"
  }'
```

#### 取得醫師資料
```bash
curl http://localhost:8000/provider/1/profile
```

#### 列出診次（帶日期篩選）
```bash
curl "http://localhost:8000/provider/1/sessions?from_date=2024-01-01&to_date=2024-12-31"
```

#### 建立/更新就診記錄
```bash
curl -X PUT "http://localhost:8000/provider/1/appointments/1/encounter" \
  -H "Content-Type: application/json" \
  -d '{
    "status": 1,
    "chief_complaint": "頭痛",
    "subjective": "患者主訴頭痛已持續三天",
    "assessment": "初步診斷為偏頭痛",
    "plan": "開立止痛藥，建議休息"
  }'
```

#### 建立/更新處方
```bash
curl -X PUT "http://localhost:8000/provider/1/encounters/1/prescription" \
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

#### 病人端 API 範例

##### 查詢可預約門診時段
```bash
curl "http://localhost:8000/patient/sessions?dept_id=1&date=2024-01-01"
```

##### 建立掛號
```bash
curl -X POST "http://localhost:8000/patient/appointments?patient_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1
  }'
```

##### 列出病人的所有掛號
```bash
curl "http://localhost:8000/patient/appointments?patient_id=1"
```

##### 取消掛號
```bash
curl -X DELETE "http://localhost:8000/patient/appointments/1?patient_id=1"
```

##### 修改掛號（改期）
```bash
curl -X PATCH "http://localhost:8000/patient/appointments/1/reschedule?patient_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "new_session_id": 2
  }'
```

##### 病人報到
```bash
curl -X POST "http://localhost:8000/patient/appointments/1/checkin?patient_id=1"
```

##### 查詢完整歷史記錄
```bash
curl "http://localhost:8000/patient/history?patient_id=1"
```

## 📚 API 端點列表

### Provider API（醫師端）

所有 Provider API 都掛載在 `/provider` 前綴下。

#### 帳號管理

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/provider/register` | 醫師註冊 |
| POST | `/provider/login` | 醫師登入 |
| GET | `/provider/{provider_id}/profile` | 取得醫師資料 |

#### 門診時段管理

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/provider/{provider_id}/sessions` | 列出診次（支援日期、狀態篩選） |
| POST | `/provider/{provider_id}/sessions` | 建立診次 |
| PUT | `/provider/{provider_id}/sessions/{session_id}` | 更新診次 |
| POST | `/provider/{provider_id}/sessions/{session_id}/cancel` | 取消診次 |

#### 預約管理

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/provider/{provider_id}/sessions/{session_id}/appointments` | 列出預約 |

#### 就診記錄

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/provider/{provider_id}/appointments/{appt_id}/encounter` | 取得就診記錄 |
| PUT | `/provider/{provider_id}/appointments/{appt_id}/encounter` | 建立/更新就診記錄 |

#### 診斷管理

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/provider/{provider_id}/encounters/{enct_id}/diagnoses` | 取得診斷列表 |
| PUT | `/provider/{provider_id}/encounters/{enct_id}/diagnoses/{code_icd}` | 建立/更新診斷 |
| POST | `/provider/{provider_id}/encounters/{enct_id}/primary-diagnosis` | 設定主要診斷 |

#### 處方管理

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/provider/{provider_id}/encounters/{enct_id}/prescription` | 取得處方 |
| PUT | `/provider/{provider_id}/encounters/{enct_id}/prescription` | 建立/更新處方 |

### Patient API（病人端）

所有 Patient API 都掛載在 `/patient` 前綴下。

#### 門診時段查詢

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/patient/sessions` | 查詢可預約的門診時段（支援科別、醫師、日期篩選） |

#### 掛號管理

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/patient/appointments` | 列出病人的所有掛號 |
| POST | `/patient/appointments` | 建立掛號（需提供 `patient_id` 和 `session_id`） |
| DELETE | `/patient/appointments/{id}` | 取消掛號（需提供 `patient_id`） |
| PATCH | `/patient/appointments/{id}/reschedule` | 修改掛號（改期，需提供 `patient_id` 和 `new_session_id`） |
| POST | `/patient/appointments/{id}/checkin` | 病人報到（需提供 `patient_id`） |

#### 歷史記錄查詢

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/patient/history` | 取得病人的完整歷史記錄（需提供 `patient_id`） |
| | | 包含：就診記錄、處方箋、檢驗結果、繳費記錄 |

## 🔐 安全說明

- 密碼使用 SHA-256 進行雜湊處理
- 所有 API 都需要正確的參數驗證
- 掛號建立使用 transaction + FOR UPDATE 避免併行衝突
- 掛號改期使用固定鎖序避免死鎖
- 建議在生產環境中使用更強的安全措施（如 JWT token、HTTPS 等）

## 🏗 架構設計

本專案採用分層架構設計：

1. **Repository Layer（資料庫操作層）**
   - 負責所有資料庫操作
   - 使用 PostgreSQL 進行資料持久化
   - 實作 Repository Pattern，提供統一的資料存取介面

2. **Service Layer（業務邏輯層）**
   - 封裝業務邏輯
   - 處理資料驗證和錯誤處理
   - 協調多個 Repository 的操作

3. **Router Layer（API 路由層）**
   - 定義 RESTful API 端點
   - 處理 HTTP 請求和回應
   - 使用 Pydantic 進行參數驗證

4. **Analytics Layer（資料分析層）**
   - 使用 DuckDB 進行高效能資料分析
   - 透過 postgres_scanner 直接查詢 PostgreSQL
   - 提供統計和分析功能

## 📝 注意事項

1. **測試前準備**：
   - 確保 PostgreSQL 資料庫已啟動並包含必要的資料表
   - 確保 `.env` 檔案中的資料庫連線設定正確
   - 確保伺服器正在運行

2. **測試 ID**：
   - 所有測試腳本中的 ID 都是範例值
   - 請根據實際資料庫內容修改這些 ID

3. **錯誤處理**：
   - 404 錯誤：資源不存在（可能是 ID 錯誤或資料庫中沒有該筆資料）
   - 400 錯誤：請求參數錯誤
   - 401 錯誤：認證失敗
   - 500 錯誤：伺服器內部錯誤（檢查伺服器日誌）

## 🐛 疑難排解

### 無法連接到伺服器
- 確認伺服器是否正在運行：`ps aux | grep uvicorn`
- 確認端口是否正確（預設為 8000）

### 資料庫連線錯誤
- 檢查 `.env` 檔案中的資料庫設定
- 確認 PostgreSQL 服務是否運行
- 確認資料庫名稱、使用者名稱、密碼是否正確

### 模組匯入錯誤
- 確認已安裝所有依賴：`pip install -r requirements.txt`
- 確認 Python 路徑設定正確

## 📄 授權

本專案為學術專題專案。

## 📊 資料分析功能

系統整合 DuckDB 進行高效能資料分析，提供以下功能：

### 病人統計分析

使用 `analytics/patient_analysis.py` 模組可以取得病人的統計資料：

- **年度就診次數**：按年份統計病人的就診次數
- **各科別就診分布**：統計病人在各科別的就診次數
- **常見診斷 top 10**：統計病人最常見的診斷（前 10 名）

使用範例：
```python
from app.analytics.patient_analysis import get_patient_statistics

# 取得病人 ID 為 1 的統計資料
stats = get_patient_statistics(patient_id=1)
print(stats)
```

## 👥 貢獻者

- Provider 端 API 實作：Hannah
- Patient 端 API 實作：已完成
- 資料分析功能：已完成

---

**最後更新**：2025-11-25