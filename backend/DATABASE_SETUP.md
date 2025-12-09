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

3. **建立資料庫索引（提升查詢效能）**
   ```bash
   psql -d dbms -f create_indexes.sql
   ```
   或使用 Python 執行：
   ```bash
   python -c "import psycopg2; from app.config import PG_DSN; conn = psycopg2.connect(PG_DSN); cur = conn.cursor(); cur.execute(open('create_indexes.sql').read()); conn.commit(); conn.close(); print('索引建立完成')"
   ```

4. **驗證設定**
   ```bash
   python check_all_sequences.py
   ```

5. **測試註冊功能**
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

## 建立資料庫索引

為了提升查詢效能，建議建立必要的索引：

### 執行索引建立腳本

```bash
cd backend
psql -d dbms -f create_indexes.sql
```

### 索引說明

`create_indexes.sql` 會建立以下索引：

- **APPOINTMENT_STATUS_HISTORY**: 用於快速查詢掛號最新狀態
- **APPOINTMENT**: 用於快速查詢病人的掛號記錄和門診時段的掛號清單
- **CLINIC_SESSION**: 用於快速查詢門診時段（根據醫師、日期、狀態篩選）
- **ENCOUNTER**: 用於快速查詢就診記錄
- **PRESCRIPTION**: 用於快速查詢處方箋
- **DIAGNOSIS**: 用於快速查詢診斷記錄
- **LAB_RESULT**: 用於快速查詢檢驗結果
- **PAYMENT**: 用於快速查詢繳費記錄
- **INCLUDE**: 用於快速查詢處方用藥明細

### 檢查已建立的索引

```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

