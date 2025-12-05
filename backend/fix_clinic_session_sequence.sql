-- 修復 CLINIC_SESSION 表的 session_id 序列

-- 1. 檢查序列是否存在
SELECT sequencename FROM pg_sequences WHERE sequencename = 'clinic_session_session_id_seq';

-- 2. 獲取當前最大 session_id
SELECT COALESCE(MAX(session_id), 0) FROM clinic_session;

-- 3. 創建序列（如果不存在）
DO $$
DECLARE
    max_id INTEGER;
    seq_exists BOOLEAN;
BEGIN
    -- 檢查序列是否存在
    SELECT EXISTS (
        SELECT 1 FROM pg_sequences WHERE sequencename = 'clinic_session_session_id_seq'
    ) INTO seq_exists;
    
    IF NOT seq_exists THEN
        -- 獲取當前最大 ID
        SELECT COALESCE(MAX(session_id), 0) INTO max_id FROM clinic_session;
        
        -- 創建序列
        EXECUTE format('CREATE SEQUENCE clinic_session_session_id_seq START %s', max_id + 1);
        
        -- 設置為 DEFAULT
        ALTER TABLE clinic_session 
        ALTER COLUMN session_id SET DEFAULT nextval('clinic_session_session_id_seq');
        
        -- 設置序列擁有者
        ALTER SEQUENCE clinic_session_session_id_seq OWNED BY clinic_session.session_id;
        
        RAISE NOTICE '序列已創建，起始值為 %', max_id + 1;
    ELSE
        RAISE NOTICE '序列已存在';
    END IF;
END $$;

-- 4. 驗證序列設定
SELECT column_name, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'clinic_session' AND column_name = 'session_id';

-- 5. 檢查序列當前值
SELECT last_value FROM clinic_session_session_id_seq;

