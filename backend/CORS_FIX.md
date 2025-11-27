# CORS 問題修復指南

## 問題

如果遇到以下錯誤：
```
Access to XMLHttpRequest at 'http://localhost:8000/...' from origin 'http://localhost:5173' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
```

## 解決方案

### 1. 確認後端伺服器已重新啟動

修改 CORS 設定後，**必須重新啟動後端伺服器**才能生效：

```bash
# 停止現有的伺服器（Ctrl+C）
# 然後重新啟動
cd backend
uvicorn app.main:app --reload
```

### 2. 檢查後端是否正在運行

```bash
# 檢查端口 8000 是否被佔用
lsof -i :8000

# 或者測試 API
curl http://localhost:8000/
```

### 3. 確認 CORS 設定

後端 `app/main.py` 應該包含：

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)
```

### 4. 測試 CORS

使用 curl 測試 CORS headers：

```bash
curl -H "Origin: http://localhost:5173" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     http://localhost:8000/provider/106/sessions \
     -v
```

應該看到 `Access-Control-Allow-Origin` header。

### 5. 瀏覽器檢查

1. 打開瀏覽器開發者工具（F12）
2. 切換到 Network 標籤
3. 找到失敗的請求
4. 檢查 Response Headers 中是否有：
   - `Access-Control-Allow-Origin: http://localhost:5173`
   - `Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS`

## 常見問題

### 問題 1：後端沒有重新啟動

**解決方案：** 重新啟動後端伺服器

### 問題 2：端口不匹配

**解決方案：** 確認前端運行在 `http://localhost:5173`，後端運行在 `http://localhost:8000`

### 問題 3：OPTIONS 請求失敗

**解決方案：** 確保 `allow_methods` 包含 `"OPTIONS"`

## 如果問題仍然存在

1. 檢查後端日誌是否有錯誤
2. 確認 FastAPI 版本是否支援 CORSMiddleware
3. 嘗試使用 `allow_origins=["*"]` 進行測試（僅開發環境）

