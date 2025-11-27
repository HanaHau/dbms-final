# 資料庫設定指南

## 初始化資料庫序列

在首次使用系統前，需要確保所有表的 ID 欄位都有正確的序列設定。

### 快速修復

執行以下腳本會自動修復所有需要的序列：

```bash
cd backend
python fix_all_sequences.py
```

### 手動檢查

檢查哪些表需要修復：

```bash
python check_all_sequences.py
```

### 需要修復的表

- ✅ `USER.user_id` → `user_user_id_seq`
- ✅ `clinic_session.session_id` → `clinic_session_session_id_seq`
- ✅ `appointment.appt_id` → `appointment_appt_id_seq`
- ✅ `encounter.enct_id` → `encounter_enct_id_seq`
- ✅ `lab_result.lab_id` → `lab_result_lab_id_seq`
- ✅ `payment.payment_id` → `payment_payment_id_seq`

## 初始化科別資料

在註冊醫師前，需要先建立科別資料：

```sql
INSERT INTO DEPARTMENT (dept_id, name) VALUES
(1, '內科'),
(2, '外科'),
(3, '兒科'),
(4, '婦產科'),
(5, '骨科')
ON CONFLICT (dept_id) DO NOTHING;
```

## 完整的初始化步驟

1. **修復所有序列**
   ```bash
   cd backend
   python fix_all_sequences.py
   ```

2. **建立科別資料**
   ```sql
   INSERT INTO DEPARTMENT (dept_id, name) VALUES
   (1, '內科'), (2, '外科'), (3, '兒科'), (4, '婦產科'), (5, '骨科')
   ON CONFLICT (dept_id) DO NOTHING;
   ```

3. **驗證設定**
   ```bash
   python check_all_sequences.py
   ```

4. **測試註冊功能**
   ```bash
   python debug_register.py provider "測試醫師" "test123" "DOC001" 1
   ```

## 常見問題

### 問題：序列已存在但 DEFAULT 未設定

**解決方案：** 執行 `fix_all_sequences.py`，它會自動檢查並設定 DEFAULT。

### 問題：序列起始值不正確

**解決方案：** 腳本會自動使用現有資料的最大 ID + 1 作為起始值。

### 問題：表名大小寫問題

**注意：** 
- `USER` 表名需要引號：`"USER"`
- 其他表名是小寫，不需要引號：`clinic_session`

