# 調試 400 Bad Request 錯誤

## 常見原因

### 1. 必填欄位缺失或為空
- 確保所有必填欄位都已填寫
- 檢查是否有空白字符

### 2. 日期格式問題
- 日期必須是 `YYYY-MM-DD` 格式（例如：`2000-01-01`）
- HTML date input 會自動產生正確格式

### 3. 數據類型錯誤
- 科別 ID 必須是正整數
- 身分證字號和執照號碼不能為空

## 如何調試

### 在瀏覽器中檢查

1. 打開瀏覽器開發者工具（F12）
2. 切換到「Network」（網路）標籤
3. 嘗試註冊
4. 找到失敗的請求（狀態碼 400）
5. 點擊該請求查看：
   - **Request Payload**：檢查發送的數據
   - **Response**：查看錯誤詳情

### 檢查請求格式

正確的病人註冊請求格式：
```json
{
  "name": "張三",
  "password": "password123",
  "national_id": "A123456789",
  "birth_date": "2000-01-01",
  "sex": "M",
  "phone": "0912345678"
}
```

正確的醫師註冊請求格式：
```json
{
  "name": "李醫師",
  "password": "password123",
  "license_no": "DOC001",
  "dept_id": 1
}
```

### 檢查後端日誌

後端會輸出詳細的錯誤信息，檢查終端機輸出。

### 常見錯誤訊息

1. **"Cannot create patient account, please check national_id"**
   - 身分證字號已存在（UNIQUE 約束）

2. **"Cannot create provider, please check license_no / dept_id"**
   - 執照號碼已存在或科別 ID 無效

3. **Pydantic 驗證錯誤**
   - 檢查字段名稱和類型是否正確
   - 檢查日期格式是否為 `YYYY-MM-DD`

## 解決方案

### 如果看到 Pydantic 驗證錯誤

檢查錯誤訊息中的字段名稱，確保：
- 字段名稱正確（例如：`birth_date` 不是 `birthDate`）
- 數據類型正確（例如：`dept_id` 是數字不是字符串）

### 如果看到資料庫錯誤

- 檢查身分證字號或執照號碼是否已存在
- 檢查科別 ID 是否存在於資料庫中

### 測試 API 端點

使用 curl 測試後端 API：

```bash
# 測試病人註冊
curl -X POST http://localhost:8000/patient/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "測試用戶",
    "password": "test123",
    "national_id": "A123456789",
    "birth_date": "2000-01-01",
    "sex": "M",
    "phone": "0912345678"
  }'

# 測試醫師註冊
curl -X POST http://localhost:8000/provider/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "測試醫師",
    "password": "test123",
    "license_no": "DOC001",
    "dept_id": 1
  }'
```

## 前端改進

已添加：
- 更詳細的錯誤訊息顯示
- 前端表單驗證
- 控制台日誌輸出（可在開發者工具中查看）

## 檢查清單

- [ ] 所有必填欄位都已填寫
- [ ] 日期格式正確（YYYY-MM-DD）
- [ ] 科別 ID 是正整數
- [ ] 身分證字號/執照號碼格式正確
- [ ] 後端 API 正在運行
- [ ] CORS 設定正確
- [ ] 檢查瀏覽器控制台是否有錯誤
- [ ] 檢查網路請求的實際發送數據

