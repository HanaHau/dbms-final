-- 修復 USER 表的 user_id 自動遞增問題

-- 1. 檢查是否已有序列
DO $$
DECLARE
    seq_exists boolean;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM pg_sequences WHERE sequencename = 'user_user_id_seq'
    ) INTO seq_exists;
    
    IF NOT seq_exists THEN
        -- 2. 建立序列
        CREATE SEQUENCE user_user_id_seq;
        
        -- 3. 設定序列的起始值（使用現有最大的 user_id + 1）
        SELECT COALESCE(MAX(user_id), 0) + 1 FROM "USER";
        PERFORM setval('user_user_id_seq', COALESCE((SELECT MAX(user_id) FROM "USER"), 0) + 1, false);
        
        -- 4. 將序列設定為 user_id 的 DEFAULT
        ALTER TABLE "USER" 
        ALTER COLUMN user_id SET DEFAULT nextval('user_user_id_seq');
        
        -- 5. 將序列的所有權給 USER 表
        ALTER SEQUENCE user_user_id_seq OWNED BY "USER".user_id;
        
        RAISE NOTICE '序列已建立並設定完成';
    ELSE
        RAISE NOTICE '序列已存在';
    END IF;
END $$;

-- 驗證設定
SELECT 
    column_name, 
    data_type, 
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'USER' AND column_name = 'user_id';

