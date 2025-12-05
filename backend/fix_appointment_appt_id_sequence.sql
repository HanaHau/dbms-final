-- 修復 APPOINTMENT.appt_id 的序列

-- 獲取當前最大的 appt_id
DO $$
DECLARE
    max_id INTEGER;
BEGIN
    -- 獲取當前最大的 appt_id
    SELECT COALESCE(MAX(appt_id), 0) INTO max_id FROM APPOINTMENT;
    
    -- 創建序列（如果不存在）
    IF NOT EXISTS (SELECT 1 FROM pg_sequences WHERE schemaname = 'public' AND sequencename = 'appointment_appt_id_seq') THEN
        CREATE SEQUENCE appointment_appt_id_seq;
    END IF;
    
    -- 設置序列的起始值為 max_id + 1
    PERFORM setval('appointment_appt_id_seq', GREATEST(max_id + 1, 1), false);
    
    -- 設置 appt_id 欄位的 DEFAULT 值
    ALTER TABLE APPOINTMENT
    ALTER COLUMN appt_id SET DEFAULT nextval('appointment_appt_id_seq');
    
    RAISE NOTICE '序列已創建並設置，起始值為 %', max_id + 1;
END $$;

-- 驗證序列設置
SELECT 
    column_name,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'appointment' AND column_name = 'appt_id';

