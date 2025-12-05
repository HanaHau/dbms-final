-- 添加 ENCOUNTER 表的鎖定欄位

-- 添加 locked_by 欄位（鎖定該 encounter 的 provider_id）
ALTER TABLE ENCOUNTER
ADD COLUMN IF NOT EXISTS locked_by BIGINT;

-- 添加 locked_at 欄位（鎖定時間）
ALTER TABLE ENCOUNTER
ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP WITH TIME ZONE;

-- 添加外鍵約束（可選，確保 locked_by 是有效的 provider）
ALTER TABLE ENCOUNTER
ADD CONSTRAINT encounter_locked_by_fkey 
FOREIGN KEY (locked_by) REFERENCES PROVIDER(user_id) 
ON DELETE SET NULL;

-- 添加註釋
COMMENT ON COLUMN ENCOUNTER.locked_by IS '鎖定該 encounter 的 provider_id（防止同時編輯）';
COMMENT ON COLUMN ENCOUNTER.locked_at IS '鎖定時間';

