# 前端設定說明

## 快速開始

### 1. 安裝依賴
```bash
cd frontend
npm install
```

### 2. 啟動開發伺服器
```bash
npm run dev
```

前端將在 `http://localhost:5173` 啟動

### 3. 確保後端 API 正在運行

後端 API 應該在 `http://localhost:8000` 運行。如果後端在不同端口，請修改 `src/services/api.ts` 中的 `API_BASE_URL`。

## 已實作的功能

### ✅ 病人端
- [x] 註冊與登入
- [x] 查詢可預約門診時段（支援篩選）
- [x] 掛號管理（新增、取消、改期、報到）
- [x] 查看完整就診記錄
- [x] 查看處方箋
- [x] 查看檢驗結果
- [x] 查看繳費記錄
- [x] 線上繳費

### ✅ 醫師端
- [x] 註冊與登入
- [x] 門診時段管理（新增、編輯、取消、篩選）
- [x] 預約管理（查看門診時段的掛號清單）
- [x] 就診記錄管理（建立/編輯，支援草稿與定稿）
- [x] 診斷管理（新增診斷、設定主要診斷）
- [x] 處方管理（建立/編輯處方箋，支援多個藥品項目）
- [x] 檢驗結果管理（新增檢驗結果）
- [x] 繳費管理（建立/更新繳費資料）

## 專案結構

```
frontend/
├── src/
│   ├── components/          # 共用組件
│   ├── context/             # React Context（認證）
│   ├── pages/                # 頁面組件
│   │   ├── patient/         # 病人端頁面
│   │   └── provider/        # 醫師端頁面
│   ├── services/            # API 服務層
│   ├── types/               # TypeScript 類型定義
│   └── App.tsx              # 主應用程式
```

## 技術細節

- **React 19** + **TypeScript** + **Vite**
- **React Router DOM** 用於路由
- **Axios** 用於 API 呼叫
- **Context API** 用於狀態管理
- **LocalStorage** 用於持久化登入狀態

## 注意事項

1. 確保後端已設定 CORS 允許前端來源
2. 後端 API 預設端口為 8000
3. 前端開發伺服器預設端口為 5173
4. 登入狀態會儲存在 localStorage 中

## 建置生產版本

```bash
npm run build
```

建置完成的檔案會在 `dist` 目錄中。

