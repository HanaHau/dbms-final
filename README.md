# 診所數位化系統 (Clinic Digital System)

一個完整的診所管理系統，包含前端（React + TypeScript）和後端（FastAPI + PostgreSQL），提供醫師端和病人端的完整功能，涵蓋帳號管理、門診時段管理、掛號管理、就診記錄、診斷與處方管理、歷史記錄查詢等功能。

## 📋 專案簡介

本專案是一個全端診所管理系統，實作了現代化的診所數位化流程：

- **醫師端**：管理門診時段、查看掛號、建立就診記錄、開立處方、記錄診斷與檢驗結果
- **病人端**：查詢門診時段、掛號、報到、查看就診記錄與處方、線上繳費

系統採用分層架構設計，使用 PostgreSQL 作為主要資料庫，並整合 DuckDB 進行資料分析。

## 🛠 技術棧

### 後端
- **框架**: FastAPI
- **資料庫**: PostgreSQL (主要資料庫)
- **分析資料庫**: DuckDB (用於資料分析)
- **Python 版本**: 3.12+
- **主要依賴**:
  - `fastapi` - Web 框架
  - `uvicorn` - ASGI 伺服器
  - `psycopg2-binary` - PostgreSQL 驅動
  - `duckdb` - 分析型資料庫
  - `python-dotenv` - 環境變數管理

### 前端
- **框架**: React 19
- **語言**: TypeScript
- **建置工具**: Vite
- **路由**: React Router DOM
- **HTTP 客戶端**: Axios
- **狀態管理**: React Context API

## 📁 專案結構

```
dbms-final/
├── backend/                          # 後端應用程式
│   ├── app/
│   │   ├── main.py                   # FastAPI 應用程式入口
│   │   ├── config.py                  # 配置管理（資料庫連線設定）
│   │   ├── pg_base.py                 # PostgreSQL 基礎功能
│   │   ├── db_duck.py                 # DuckDB 分析功能
│   │   ├── lib/
│   │   │   └── period_utils.py        # 門診時段工具函數
│   │   ├── repositories/              # 資料庫操作層（Repository Pattern）
│   │   │   ├── provider_repo.py
│   │   │   ├── patient_repo.py
│   │   │   ├── session_repo.py
│   │   │   ├── appointment_repo.py
│   │   │   ├── encounter_repo.py
│   │   │   ├── diagnosis_repo.py
│   │   │   ├── prescription_repo.py
│   │   │   ├── lab_result_repo.py
│   │   │   └── payment_repo.py
│   │   ├── services/                  # 業務邏輯層（Service Layer）
│   │   │   ├── provider_service.py
│   │   │   ├── patient_service.py
│   │   │   ├── patient_history_service.py
│   │   │   └── shared/
│   │   │       ├── appointment_service.py
│   │   │       └── session_service.py
│   │   ├── routers/                   # API 路由層
│   │   │   ├── provider_router.py
│   │   │   └── patient_router.py
│   │   └── analytics/                 # 資料分析功能
│   │       └── patient_analysis.py
│   ├── requirements.txt                # Python 依賴套件
│   ├── fix_all_sequences.py            # 修復所有表的 ID 序列
│   ├── check_all_sequences.py          # 檢查序列設定
│   ├── create_indexes.sql              # 建立資料庫索引（提升查詢效能）
│   ├── debug_register.py               # 測試註冊功能
│   ├── DATABASE_SETUP.md               # 資料庫設定指南
│   └── CORS_FIX.md                     # CORS 問題修復指南
│
├── frontend/                          # 前端應用程式
│   ├── src/
│   │   ├── components/                # 共用組件
│   │   │   ├── Layout.tsx
│   │   │   ├── DepartmentCard.tsx
│   │   │   └── ...
│   │   ├── pages/                      # 頁面組件
│   │   │   ├── Home.tsx
│   │   │   ├── patient/               # 病人端頁面
│   │   │   │   ├── PatientLogin.tsx
│   │   │   │   ├── PatientRegister.tsx
│   │   │   │   ├── PatientAppointments.tsx
│   │   │   │   ├── PatientHistory.tsx
│   │   │   │   └── PatientPayments.tsx
│   │   │   └── provider/              # 醫師端頁面
│   │   │       ├── ProviderLogin.tsx
│   │   │       ├── ProviderRegister.tsx
│   │   │       ├── ProviderSessions.tsx
│   │   │       ├── ProviderAppointments.tsx
│   │   │       └── ProviderEncounter.tsx
│   │   ├── services/
│   │   │   └── api.ts                 # API 服務層
│   │   ├── types/
│   │   │   └── index.ts               # TypeScript 類型定義
│   │   ├── lib/                       # 工具函數
│   │   │   ├── periodUtils.ts         # 門診時段工具
│   │   │   ├── dateFormat.ts
│   │   │   └── ...
│   │   ├── context/
│   │   │   └── AuthContext.tsx        # 認證上下文
│   │   ├── App.tsx                    # 主應用程式（路由設定）
│   │   └── main.tsx                   # 應用程式入口
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

## ✨ 核心功能

### 1. 帳號管理
- ✅ 病人註冊與登入
- ✅ 醫師註冊與登入
- ✅ 個人資料查詢

### 2. 門診時段管理（醫師端）
- ✅ 建立門診時段（使用固定時段：早診、午診、晚診）
- ✅ 編輯門診時段
- ✅ 取消門診時段
- ✅ 查詢門診時段（支援日期範圍、狀態篩選）
- ✅ 自動過期時段處理
- ✅ 時段重疊檢查（同一醫師同一日期不能有相同時段）

**時段定義**：
- **早診** (period=1): 09:00-12:00
- **午診** (period=2): 14:00-17:00
- **晚診** (period=3): 18:00-21:00

### 3. 掛號管理
- ✅ 查詢可預約門診時段（支援科別、醫師、日期篩選）
- ✅ 建立掛號（自動檢查容量、避免重複掛號）
- ✅ 取消掛號
- ✅ 改期（修改掛號時段）
- ✅ 病人報到（僅允許在門診時間內報到）
- ✅ 自動過號機制（當前面所有掛號都已完成/取消/過號時，自動標記為過號）
- ✅ 爽約管理（累計爽約次數，達到 3 次則禁止掛號 2 週）

**掛號狀態**：
- `1`: 已預約 (booked)
- `2`: 已報到 (checked_in)
- `3`: 已完成 (completed)
- `4`: 已取消 (cancelled)
- `5`: 已過號 (no_show)
- `6`: 候補 (waitlisted)

### 4. 就診記錄管理（醫師端）
- ✅ 建立就診記錄（主訴、主觀描述、評估、計畫）
- ✅ 編輯就診記錄（支援草稿與定稿狀態）
- ✅ 查看病人歷史就診記錄
- ✅ 時間驗證（僅允許在門診時間內建立就診記錄）

### 5. 診斷管理
- ✅ 新增診斷（支援 ICD 代碼）
- ✅ 設定主要診斷
- ✅ 查看診斷列表
- ✅ 查看病人歷史診斷

### 6. 處方管理
- ✅ 建立處方（支援多個藥品項目）
- ✅ 編輯處方項目
- ✅ 查看處方內容
- ✅ 處方開立後即完成（無需狀態追蹤）

**處方項目包含**：
- 藥品名稱
- 劑量
- 頻率
- 天數
- 數量

### 7. 檢驗報告管理
- ✅ 新增檢驗結果
- ✅ 查看檢驗結果列表
- ✅ 檢驗結果包含：LOINC 代碼、項目名稱、數值、單位、參考範圍、異常標記

### 8. 繳費管理
- ✅ 建立繳費資料
- ✅ 更新繳費資料
- ✅ 線上繳費（支援現金、信用卡、保險）
- ✅ 查看繳費記錄

### 9. 歷史記錄查詢
- ✅ 病人完整歷史記錄（就診記錄、診斷、處方、檢驗結果、繳費記錄）
- ✅ 醫師查看病人歷史記錄

### 10. 資料分析
- ✅ DuckDB 整合
- ✅ 病人統計分析（年度就診次數、科別分布、常見診斷）

## 🚀 快速開始

### 前置需求

- Python 3.12+
- Node.js 18+
- PostgreSQL 14+
- npm 或 yarn

### 1. 資料庫設定

#### 建立資料庫
```bash
createdb dbms
```

#### 設定環境變數

在 `backend` 目錄下建立 `.env` 檔案：

```env
PG_HOST=localhost
PG_PORT=5432
PG_DB=dbms
PG_USER=your_username
PG_PASSWORD=your_password
```

#### 初始化資料庫

執行資料庫 schema 建立腳本（請參考 `backend/DATABASE_SETUP.md`）。

**重要：建立索引以提升查詢效能**

```bash
cd backend
psql -d dbms -f create_indexes.sql
```

此腳本會建立必要的索引，大幅提升查詢效能，特別是：
- 掛號狀態查詢
- 病人掛號記錄查詢
- 門診時段搜尋
- 就診記錄查詢

### 2. 後端設定

#### 安裝依賴
```bash
cd backend
pip install -r requirements.txt
```

#### 啟動後端伺服器
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

後端 API 將在 `http://localhost:8000` 啟動。

**API 文檔**：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. 前端設定

#### 安裝依賴
```bash
cd frontend
npm install
```

#### 啟動前端開發伺服器
```bash
npm run dev
```

前端應用程式將在 `http://localhost:5173` 啟動。

### 4. 資料生成（可選）

如果需要測試資料，可以使用資料生成腳本：

```bash
cd backend
python3 generate_data.py
```

## 📚 API 文檔

### Provider API（醫師端）

所有 Provider API 都掛載在 `/provider` 前綴下。

#### 帳號管理
- `POST /provider/register` - 醫師註冊
- `POST /provider/login` - 醫師登入
- `GET /provider/{provider_id}/profile` - 取得醫師資料

#### 門診時段管理
- `GET /provider/{provider_id}/sessions` - 列出診次（支援日期、狀態篩選）
- `POST /provider/{provider_id}/sessions` - 建立診次
  ```json
  {
    "date": "2024-01-01",
    "period": 1,  // 1=早診, 2=午診, 3=晚診
    "capacity": 20
  }
  ```
- `PUT /provider/{provider_id}/sessions/{session_id}` - 更新診次
- `POST /provider/{provider_id}/sessions/{session_id}/cancel` - 取消診次

#### 預約管理
- `GET /provider/{provider_id}/sessions/{session_id}/appointments` - 列出預約

#### 就診記錄
- `GET /provider/{provider_id}/appointments/{appt_id}/encounter` - 取得就診記錄
- `PUT /provider/{provider_id}/appointments/{appt_id}/encounter` - 建立/更新就診記錄

#### 診斷管理
- `GET /provider/{provider_id}/encounters/{enct_id}/diagnoses` - 取得診斷列表
- `PUT /provider/{provider_id}/encounters/{enct_id}/diagnoses/{code_icd}` - 建立/更新診斷
- `POST /provider/{provider_id}/encounters/{enct_id}/primary-diagnosis` - 設定主要診斷

#### 處方管理
- `GET /provider/{provider_id}/encounters/{enct_id}/prescription` - 取得處方
- `PUT /provider/{provider_id}/encounters/{enct_id}/prescription` - 建立/更新處方
  ```json
  {
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

#### 檢驗報告管理
- `GET /provider/{provider_id}/encounters/{enct_id}/lab-results` - 取得檢驗結果列表
- `POST /provider/{provider_id}/encounters/{enct_id}/lab-results` - 新增檢驗結果

#### 繳費管理
- `GET /provider/{provider_id}/encounters/{enct_id}/payment` - 取得繳費資訊
- `POST /provider/{provider_id}/encounters/{enct_id}/payment` - 建立/更新繳費資料

#### 病人歷史記錄
- `GET /provider/{provider_id}/patients/{patient_id}/history` - 查詢病人完整歷史記錄

### Patient API（病人端）

所有 Patient API 都掛載在 `/patient` 前綴下。

#### 帳號管理
- `POST /patient/register` - 病人註冊
- `POST /patient/login` - 病人登入
- `GET /patient/{patient_id}/profile` - 取得病人資料

#### 門診時段查詢
- `GET /patient/sessions` - 查詢可預約的門診時段（支援科別、醫師、日期篩選）

#### 掛號管理
- `GET /patient/appointments` - 列出病人的所有掛號
- `POST /patient/appointments` - 建立掛號
  ```json
  {
    "session_id": 1
  }
  ```
- `DELETE /patient/appointments/{id}` - 取消掛號
- `PATCH /patient/appointments/{id}/reschedule` - 修改掛號（改期）
- `POST /patient/appointments/{id}/checkin` - 病人報到

#### 歷史記錄查詢
- `GET /patient/history` - 取得病人的完整歷史記錄

#### 繳費管理
- `GET /patient/payments` - 列出繳費記錄
- `POST /patient/payments/{payment_id}/pay` - 線上繳費

## 🗄 資料庫結構

### 核心資料表

- **USER** - 使用者基本資料
- **PROVIDER** - 醫師資料
- **PATIENT** - 病人資料（包含 `no_show_count`、`banned_until`）
- **DEPARTMENT** - 科別資料（包含 `category_id`）
- **DEPARTMENT_CATEGORY** - 科別分類（內科系、外科系、婦幼科、五官科、精神科、牙科、其他）
- **CLINIC_SESSION** - 門診時段（使用 `period` 欄位：1=早診, 2=午診, 3=晚診）
- **APPOINTMENT** - 掛號記錄（包含 `slot_seq` 連續編號）
- **APPOINTMENT_STATUS_HISTORY** - 掛號狀態歷史
- **ENCOUNTER** - 就診記錄
- **DIAGNOSIS** - 診斷記錄
- **DISEASE** - 疾病資料（使用 `description` 欄位）
- **PRESCRIPTION** - 處方箋（無 `status` 欄位）
- **INCLUDE** - 處方用藥明細
- **MEDICATION** - 藥品資料
- **LAB_RESULT** - 檢驗結果
- **PAYMENT** - 繳費記錄

### 重要約束

- **CLINIC_SESSION**: `(provider_id, date, period)` 唯一約束
- **APPOINTMENT**: `slot_seq` 在每個 session 中連續編號
- **掛號狀態**: 只能遞增，不能倒退
- **有 encounter 的 appointment**: 狀態必須是 `completed` (3)

## 🔐 安全與驗證

### 密碼處理
- 使用 SHA-256 進行雜湊處理
- 所有帳號預設密碼：`password123`（測試環境）

### 併發控制
- 掛號建立使用 `transaction + FOR UPDATE` 避免併行衝突
- 掛號改期使用固定鎖序避免死鎖

### 時間驗證
- 病人報到：僅允許在門診時間內報到
- 建立就診記錄：僅允許在門診時間內建立
- 門診時段過期：自動更新狀態為停診

### 業務規則
- 同一醫師同一日期不能有相同時段（period）的門診
- 掛號數量不能超過 session capacity
- 已過號的病人可以報到
- 爽約 3 次則禁止掛號 2 週

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

## 📝 重要變更說明

### 1. 門診時段固定化
- **變更前**: 使用 `start_time` 和 `end_time` (TIME 類型)
- **變更後**: 使用 `period` (SMALLINT, 1=早診, 2=午診, 3=晚診)
- **影響**: 所有 API 和前端介面已更新

### 2. 處方狀態移除
- **變更前**: PRESCRIPTION 表有 `status` 欄位
- **變更後**: 移除 `status` 欄位，處方開立後即完成
- **影響**: 處方管理 API 和前端已更新

### 3. 疾病描述欄位
- **變更前**: DISEASE 表使用 `desc` 欄位（PostgreSQL 關鍵字）
- **變更後**: 使用 `description` 欄位
- **影響**: 所有相關查詢已更新

### 4. 科別分類
- **新增**: DEPARTMENT_CATEGORY 表
- **影響**: DEPARTMENT 表新增 `category_id` 外鍵

### 5. 爽約機制
- **新增**: PATIENT 表新增 `no_show_count` 和 `banned_until` 欄位
- **功能**: 自動累計爽約次數，達到 3 次則禁止掛號 2 週

## 🧪 測試

### API 測試

#### 使用 Swagger UI（推薦）
1. 啟動後端伺服器
2. 訪問 http://localhost:8000/docs
3. 在 Swagger UI 中測試各個 API 端點

#### 使用 curl
```bash
# 醫師登入
curl -X POST "http://localhost:8000/provider/login" \
  -H "Content-Type: application/json" \
  -d '{"license_no": "DOC001", "password": "password123"}'

# 建立門診時段
curl -X POST "http://localhost:8000/provider/1/sessions" \
  -H "Content-Type: application/json" \
  -d '{"date": "2024-01-01", "period": 1, "capacity": 20}'
```

### 前端測試
1. 啟動前端開發伺服器
2. 訪問 http://localhost:5173
3. 使用測試帳號登入進行功能測試

## 🐛 疑難排解

### 後端問題

**無法連接到伺服器**
- 確認伺服器是否正在運行：`ps aux | grep uvicorn`
- 確認端口是否正確（預設為 8000）

**資料庫連線錯誤**
- 檢查 `.env` 檔案中的資料庫設定
- 確認 PostgreSQL 服務是否運行
- 確認資料庫名稱、使用者名稱、密碼是否正確

**模組匯入錯誤**
- 確認已安裝所有依賴：`pip install -r requirements.txt`
- 確認 Python 路徑設定正確

### 前端問題

**API 連線失敗**
- 確認後端伺服器正在運行
- 檢查 `src/services/api.ts` 中的 `API_BASE_URL` 設定
- 確認 CORS 設定正確

**頁面無法載入**
- 確認已安裝所有依賴：`npm install`
- 檢查瀏覽器控制台錯誤訊息

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

## 📄 授權

本專案為學術專題專案。

## 👥 貢獻者

- 後端 API 實作：Hannah
- 前端應用程式實作：Hannah
- 資料分析功能：Hannah

---

**最後更新**：2025-01-XX
