-- 修復 CLINIC_SESSION 表的 status CHECK 約束
-- 根據新的資料庫設計，status 只能是 0（停診）或 1（開診）

-- 1. 檢查現有的約束
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'clinic_session'::regclass
  AND contype = 'c'
  AND conname LIKE '%status%';

-- 2. 刪除現有的 status 約束（如果存在）
ALTER TABLE clinic_session DROP CONSTRAINT IF EXISTS clinic_session_status_check;

-- 3. 添加新的約束：status 只能是 0 或 1
ALTER TABLE clinic_session
ADD CONSTRAINT clinic_session_status_check
CHECK (status IN (0, 1));

-- 4. 驗證約束
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'clinic_session'::regclass
  AND contype = 'c'
  AND conname = 'clinic_session_status_check';

-- 5. 檢查是否有違反約束的資料
SELECT session_id, provider_id, date, period, capacity, status
FROM clinic_session
WHERE status NOT IN (0, 1);

-- 6. 如果發現違反約束的資料，可以執行以下語句將它們更新為 0（停診）
-- UPDATE clinic_session SET status = 0 WHERE status NOT IN (0, 1);

