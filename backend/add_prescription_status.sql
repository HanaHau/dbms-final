-- 添加 PRESCRIPTION 表的 status 欄位

-- 添加 status 欄位（1=草稿，2=已定稿）
ALTER TABLE PRESCRIPTION
ADD COLUMN IF NOT EXISTS status SMALLINT DEFAULT 1 NOT NULL;

-- 將現有的處方都設為已定稿（2）
UPDATE PRESCRIPTION
SET status = 2
WHERE status = 1;

-- 添加 CHECK 約束
ALTER TABLE PRESCRIPTION
ADD CONSTRAINT prescription_status_check CHECK (status IN (1, 2));

-- 添加註釋
COMMENT ON COLUMN PRESCRIPTION.status IS '處方狀態：1=草稿，2=已定稿';

