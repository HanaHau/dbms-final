-- 添加 PATIENT 表的 no_show_count 和 banned_until 欄位

-- 添加 no_show_count 欄位（預設值為 0）
ALTER TABLE PATIENT
ADD COLUMN IF NOT EXISTS no_show_count INTEGER DEFAULT 0 NOT NULL;

-- 添加 banned_until 欄位（可為 NULL）
ALTER TABLE PATIENT
ADD COLUMN IF NOT EXISTS banned_until DATE;

-- 添加註釋說明
COMMENT ON COLUMN PATIENT.no_show_count IS '病人爽約次數';
COMMENT ON COLUMN PATIENT.banned_until IS '禁止掛號截止日期（達到三次爽約後設置為兩週後）';

