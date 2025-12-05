-- Migration: 將 CLINIC_SESSION 從 start_time/end_time 遷移到 period
-- 步驟：
-- 1. 添加 period 欄位
-- 2. 根據現有的 start_time/end_time 計算 period 值
-- 3. 設置 NOT NULL 約束
-- 4. 添加 UNIQUE 約束 (provider_id, date, period)
-- 5. 刪除 start_time 和 end_time 欄位（可選，建議先保留一段時間）

-- 1. 檢查現有表結構
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'clinic_session'
ORDER BY ordinal_position;

-- 2. 添加 period 欄位（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'clinic_session' AND column_name = 'period'
    ) THEN
        ALTER TABLE clinic_session ADD COLUMN period SMALLINT;
        RAISE NOTICE 'Added period column';
    ELSE
        RAISE NOTICE 'period column already exists';
    END IF;
END $$;

-- 3. 根據 start_time 和 end_time 計算 period 值
-- period: 1=早診(09:00-12:00), 2=午診(14:00-17:00), 3=晚診(18:00-21:00)
UPDATE clinic_session
SET period = CASE
    WHEN start_time = TIME '09:00:00' AND end_time = TIME '12:00:00' THEN 1  -- 早診
    WHEN start_time = TIME '14:00:00' AND end_time = TIME '17:00:00' THEN 2  -- 午診
    WHEN start_time = TIME '18:00:00' AND end_time = TIME '21:00:00' THEN 3  -- 晚診
    -- 對於無法精確匹配的時段，根據 start_time 推斷
    WHEN start_time >= TIME '09:00:00' AND start_time < TIME '12:00:00' THEN 1  -- 早診範圍
    WHEN start_time >= TIME '14:00:00' AND start_time < TIME '17:00:00' THEN 2  -- 午診範圍
    WHEN start_time >= TIME '18:00:00' AND start_time < TIME '21:00:00' THEN 3  -- 晚診範圍
    ELSE 1  -- 預設為早診
END
WHERE period IS NULL;

-- 4. 檢查是否有無法匹配的時段
SELECT session_id, provider_id, date, start_time, end_time, period
FROM clinic_session
WHERE period IS NULL;

-- 6. 設置 NOT NULL 約束
ALTER TABLE clinic_session ALTER COLUMN period SET NOT NULL;

-- 7. 刪除舊的 UNIQUE 約束（如果存在）
ALTER TABLE clinic_session DROP CONSTRAINT IF EXISTS clinic_session_provider_id_date_start_time_key;
ALTER TABLE clinic_session DROP CONSTRAINT IF EXISTS clinic_session_provider_id_date_end_time_key;

-- 8. 添加新的 UNIQUE 約束 (provider_id, date, period)
ALTER TABLE clinic_session
ADD CONSTRAINT clinic_session_provider_date_period_unique
UNIQUE (provider_id, date, period);

-- 9. 驗證結果
SELECT 
    period,
    COUNT(*) as count,
    MIN(start_time) as min_start,
    MAX(start_time) as max_start,
    MIN(end_time) as min_end,
    MAX(end_time) as max_end
FROM clinic_session
GROUP BY period
ORDER BY period;

-- 10. 顯示最終表結構
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'clinic_session'
ORDER BY ordinal_position;

