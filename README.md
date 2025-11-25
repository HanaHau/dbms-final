# Clinic Digital System API

一個基於 FastAPI 的診所數位化系統後端 API，提供醫師端（Provider）的完整功能，包括帳號管理、門診時段管理、就診記錄、診斷與處方管理等。

## 📋 專案簡介

本專案是一個診所管理系統的後端 API，主要實作了醫師端的功能。系統使用 PostgreSQL 作為主要資料庫，並整合 DuckDB 進行資料分析。所有 API 遵循 RESTful 設計原則，並提供完整的 Swagger 文檔。

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
│   │   ├── main.py              # FastAPI 應用程式入口
│   │   ├── config.py             # 配置管理（資料庫連線設定）
│   │   ├── pg_base.py            # PostgreSQL 基礎功能（連線、ID 生成）
│   │   ├── pg_provider.py        # Provider 相關的資料庫操作函數
│   │   ├── router_provider.py    # Provider API 路由定義
│   │   └── db_duck.py            # DuckDB 分析功能
│   ├── requirements.txt          # Python 依賴套件
│   ├── test_api.py               # Python API 測試腳本
│   └── test_api.sh               # Shell API 測試腳本
└── README.md
```

## ✨ 已實作功能

### 1. 帳號管理
- ✅ 醫師註冊 (`POST /provider/register`)
- ✅ 醫師登入 (`POST /provider/login`)
- ✅ 取得醫師資料 (`GET /provider/{provider_id}/profile`)

### 2. 門診時段管理
- ✅ 列出診次 (`GET /provider/{provider_id}/sessions`)
  - 支援日期範圍篩選
  - 支援狀態篩選
- ✅ 建立診次 (`POST /provider/{provider_id}/sessions`)
- ✅ 更新診次 (`PUT /provider/{provider_id}/sessions/{session_id}`)
- ✅ 取消診次 (`POST /provider/{provider_id}/sessions/{session_id}/cancel`)

### 3. 預約管理
- ✅ 列出預約 (`GET /provider/{provider_id}/sessions/{session_id}/appointments`)

### 4. 就診記錄（Encounter）
- ✅ 取得就診記錄 (`GET /provider/{provider_id}/appointments/{appt_id}/encounter`)
- ✅ 建立/更新就診記錄 (`PUT /provider/{provider_id}/appointments/{appt_id}/encounter`)
  - 包含主訴、主觀描述、評估、計畫等欄位

### 5. 診斷管理
- ✅ 取得診斷列表 (`GET /provider/{provider_id}/encounters/{enct_id}/diagnoses`)
- ✅ 建立/更新診斷 (`PUT /provider/{provider_id}/encounters/{enct_id}/diagnoses/{code_icd}`)
- ✅ 設定主要診斷 (`POST /provider/{provider_id}/encounters/{enct_id}/primary-diagnosis`)

### 6. 處方管理
- ✅ 取得處方 (`GET /provider/{provider_id}/encounters/{enct_id}/prescription`)
- ✅ 建立/更新處方 (`PUT /provider/{provider_id}/encounters/{enct_id}/prescription`)
  - 支援多個藥品項目
  - 每個項目包含劑量、頻率、天數、數量等資訊

### 7. 資料分析
- ✅ DuckDB 整合（用於資料分析查詢）
- ✅ 每日看診統計功能

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
- `USER`
- `PROVIDER`
- `DEPARTMENT`
- `CLINIC_SESSION`
- `APPOINTMENT`
- `ENCOUNTER`
- `DIAGNOSIS`
- `PRESCRIPTION`
- `PRESCRIPTION_ITEM`
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

## 📚 API 端點列表

所有 Provider API 都掛載在 `/provider` 前綴下。

### 帳號管理

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/provider/register` | 醫師註冊 |
| POST | `/provider/login` | 醫師登入 |
| GET | `/provider/{provider_id}/profile` | 取得醫師資料 |

### 門診時段管理

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/provider/{provider_id}/sessions` | 列出診次（支援日期、狀態篩選） |
| POST | `/provider/{provider_id}/sessions` | 建立診次 |
| PUT | `/provider/{provider_id}/sessions/{session_id}` | 更新診次 |
| POST | `/provider/{provider_id}/sessions/{session_id}/cancel` | 取消診次 |

### 預約管理

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/provider/{provider_id}/sessions/{session_id}/appointments` | 列出預約 |

### 就診記錄

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/provider/{provider_id}/appointments/{appt_id}/encounter` | 取得就診記錄 |
| PUT | `/provider/{provider_id}/appointments/{appt_id}/encounter` | 建立/更新就診記錄 |

### 診斷管理

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/provider/{provider_id}/encounters/{enct_id}/diagnoses` | 取得診斷列表 |
| PUT | `/provider/{provider_id}/encounters/{enct_id}/diagnoses/{code_icd}` | 建立/更新診斷 |
| POST | `/provider/{provider_id}/encounters/{enct_id}/primary-diagnosis` | 設定主要診斷 |

### 處方管理

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/provider/{provider_id}/encounters/{enct_id}/prescription` | 取得處方 |
| PUT | `/provider/{provider_id}/encounters/{enct_id}/prescription` | 建立/更新處方 |

## 🔐 安全說明

- 密碼使用 SHA-256 進行雜湊處理
- 所有 API 都需要正確的參數驗證
- 建議在生產環境中使用更強的安全措施（如 JWT token、HTTPS 等）

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

## 👥 貢獻者

- Provider 端 API 實作：Hannah
- Patient 端 API：待組員實作

---

**最後更新**: 2024

