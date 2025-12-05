-- 修復 LAB_RESULT.lab_id 的序列

-- 獲取當前最大的 lab_id
DO $$
DECLARE
    max_id INTEGER;
BEGIN
    -- 獲取當前最大的 lab_id
    SELECT COALESCE(MAX(lab_id), 0) INTO max_id FROM LAB_RESULT;
    
    -- 創建序列（如果不存在）
    IF NOT EXISTS (SELECT 1 FROM pg_sequences WHERE schemaname = 'public' AND sequencename = 'lab_result_lab_id_seq') THEN
        CREATE SEQUENCE lab_result_lab_id_seq;
    END IF;
    
    -- 設置序列的起始值為 max_id + 1
    PERFORM setval('lab_result_lab_id_seq', GREATEST(max_id + 1, 1), false);
    
    -- 設置 lab_id 欄位的 DEFAULT 值
    ALTER TABLE LAB_RESULT
    ALTER COLUMN lab_id SET DEFAULT nextval('lab_result_lab_id_seq');
    
    -- 將序列的所有權給 LAB_RESULT 表
    ALTER SEQUENCE lab_result_lab_id_seq OWNED BY LAB_RESULT.lab_id;
    
    RAISE NOTICE '序列已創建並設置，起始值為 %', max_id + 1;
END $$;

-- 驗證序列設置
SELECT 
    column_name,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'lab_result' AND column_name = 'lab_id';

