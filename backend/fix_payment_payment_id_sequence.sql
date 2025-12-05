-- 修復 PAYMENT.payment_id 的序列

-- 獲取當前最大的 payment_id
DO $$
DECLARE
    max_id INTEGER;
BEGIN
    -- 獲取當前最大的 payment_id
    SELECT COALESCE(MAX(payment_id), 0) INTO max_id FROM PAYMENT;
    
    -- 創建序列（如果不存在）
    IF NOT EXISTS (SELECT 1 FROM pg_sequences WHERE schemaname = 'public' AND sequencename = 'payment_payment_id_seq') THEN
        CREATE SEQUENCE payment_payment_id_seq;
    END IF;
    
    -- 設置序列的起始值為 max_id + 1
    PERFORM setval('payment_payment_id_seq', GREATEST(max_id + 1, 1), false);
    
    -- 設置 payment_id 欄位的 DEFAULT 值
    ALTER TABLE PAYMENT
    ALTER COLUMN payment_id SET DEFAULT nextval('payment_payment_id_seq');
    
    -- 將序列的所有權給 PAYMENT 表
    ALTER SEQUENCE payment_payment_id_seq OWNED BY PAYMENT.payment_id;
    
    RAISE NOTICE '序列已創建並設置，起始值為 %', max_id + 1;
END $$;

-- 驗證序列設置
SELECT 
    column_name,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'payment' AND column_name = 'payment_id';

