-- ============================================================
-- 資料庫索引建立腳本
-- ============================================================
-- 此腳本用於建立必要的索引以提升查詢效能
-- 執行方式：psql -d dbms -f create_indexes.sql
-- ============================================================

-- ============================================================
-- 1. APPOINTMENT_STATUS_HISTORY 表索引
-- ============================================================
-- 用於快速查詢掛號的最新狀態（ORDER BY changed_at DESC）

-- 複合索引：用於查詢特定掛號的最新狀態
CREATE INDEX IF NOT EXISTS idx_appointment_status_history_appt_id_changed_at 
ON APPOINTMENT_STATUS_HISTORY(appt_id, changed_at DESC);

-- 單獨索引：用於 JOIN 操作
CREATE INDEX IF NOT EXISTS idx_appointment_status_history_appt_id 
ON APPOINTMENT_STATUS_HISTORY(appt_id);

-- ============================================================
-- 2. APPOINTMENT 表索引
-- ============================================================
-- 用於快速查詢病人的掛號記錄和門診時段的掛號清單

-- 病人 ID 索引：用於查詢特定病人的所有掛號
CREATE INDEX IF NOT EXISTS idx_appointment_patient_id 
ON APPOINTMENT(patient_id);

-- 門診時段 ID 索引：用於查詢特定門診時段的所有掛號
CREATE INDEX IF NOT EXISTS idx_appointment_session_id 
ON APPOINTMENT(session_id);

-- 複合索引：用於查詢門診時段的掛號並按順序排列
CREATE INDEX IF NOT EXISTS idx_appointment_session_id_slot_seq 
ON APPOINTMENT(session_id, slot_seq);

-- 複合索引：用於查詢特定病人在特定門診時段的掛號
CREATE INDEX IF NOT EXISTS idx_appointment_patient_session 
ON APPOINTMENT(patient_id, session_id);

-- ============================================================
-- 3. CLINIC_SESSION 表索引
-- ============================================================
-- 用於快速查詢門診時段（根據醫師、日期、狀態篩選）

-- 醫師 ID 索引：用於查詢特定醫師的所有門診時段
CREATE INDEX IF NOT EXISTS idx_clinic_session_provider_id 
ON CLINIC_SESSION(provider_id);

-- 日期索引：用於查詢特定日期的門診時段
CREATE INDEX IF NOT EXISTS idx_clinic_session_date 
ON CLINIC_SESSION(date);

-- 狀態索引：用於篩選開診/停診的門診時段
CREATE INDEX IF NOT EXISTS idx_clinic_session_status 
ON CLINIC_SESSION(status);

-- 複合索引：用於查詢特定醫師在特定日期的門診時段
CREATE INDEX IF NOT EXISTS idx_clinic_session_provider_date 
ON CLINIC_SESSION(provider_id, date);

-- 複合索引：用於查詢特定日期和狀態的門診時段
CREATE INDEX IF NOT EXISTS idx_clinic_session_date_status 
ON CLINIC_SESSION(date, status);

-- 複合索引：用於查詢特定醫師、日期和狀態的門診時段
CREATE INDEX IF NOT EXISTS idx_clinic_session_provider_date_status 
ON CLINIC_SESSION(provider_id, date, status);

-- 注意：(provider_id, date, period) 的唯一約束應該已經自動建立索引

-- ============================================================
-- 4. ENCOUNTER 表索引
-- ============================================================
-- 用於快速查詢就診記錄

-- 掛號 ID 索引：用於 JOIN APPOINTMENT 表
CREATE INDEX IF NOT EXISTS idx_encounter_appt_id 
ON ENCOUNTER(appt_id);

-- 醫師 ID 索引：用於查詢特定醫師的就診記錄
CREATE INDEX IF NOT EXISTS idx_encounter_provider_id 
ON ENCOUNTER(provider_id);

-- 複合索引：用於查詢特定醫師對特定病人的就診記錄
CREATE INDEX IF NOT EXISTS idx_encounter_provider_patient 
ON ENCOUNTER(provider_id, appt_id);

-- 就診時間索引：用於按時間排序
CREATE INDEX IF NOT EXISTS idx_encounter_encounter_at 
ON ENCOUNTER(encounter_at DESC);

-- ============================================================
-- 5. PRESCRIPTION 表索引
-- ============================================================
-- 用於快速查詢處方箋

-- 就診記錄 ID 索引：用於查詢特定就診記錄的處方
CREATE INDEX IF NOT EXISTS idx_prescription_enct_id 
ON PRESCRIPTION(enct_id);

-- ============================================================
-- 6. PROVIDER 表索引
-- ============================================================
-- 用於快速查詢醫師資訊

-- 科別 ID 索引：用於查詢特定科別的所有醫師
CREATE INDEX IF NOT EXISTS idx_provider_dept_id 
ON PROVIDER(dept_id);

-- 執照號碼索引：用於登入驗證（應該有唯一約束）
-- 如果已有唯一約束，則不需要額外索引

-- ============================================================
-- 7. PATIENT 表索引
-- ============================================================
-- 用於快速查詢病人資訊

-- 身分證字號索引：用於登入驗證（應該有唯一約束）
-- 如果已有唯一約束，則不需要額外索引

-- ============================================================
-- 8. DIAGNOSIS 表索引
-- ============================================================
-- 用於快速查詢診斷記錄

-- 就診記錄 ID 索引：用於查詢特定就診記錄的所有診斷
CREATE INDEX IF NOT EXISTS idx_diagnosis_enct_id 
ON DIAGNOSIS(enct_id);

-- 疾病代碼索引：用於查詢特定疾病的診斷記錄
CREATE INDEX IF NOT EXISTS idx_diagnosis_code_icd 
ON DIAGNOSIS(code_icd);

-- 主要診斷索引：用於查詢主要診斷
CREATE INDEX IF NOT EXISTS idx_diagnosis_is_primary 
ON DIAGNOSIS(is_primary) WHERE is_primary = TRUE;

-- ============================================================
-- 9. LAB_RESULT 表索引
-- ============================================================
-- 用於快速查詢檢驗結果

-- 就診記錄 ID 索引：用於查詢特定就診記錄的所有檢驗結果
CREATE INDEX IF NOT EXISTS idx_lab_result_enct_id 
ON LAB_RESULT(enct_id);

-- ============================================================
-- 10. PAYMENT 表索引
-- ============================================================
-- 用於快速查詢繳費記錄

-- 就診記錄 ID 索引：用於查詢特定就診記錄的繳費資訊
CREATE INDEX IF NOT EXISTS idx_payment_enct_id 
ON PAYMENT(enct_id);

-- ============================================================
-- 11. INCLUDE 表索引（處方用藥明細）
-- ============================================================
-- 用於快速查詢處方用藥明細

-- 處方 ID 索引：用於查詢特定處方的所有用藥明細
CREATE INDEX IF NOT EXISTS idx_include_rx_id 
ON INCLUDE(rx_id);

-- 藥品 ID 索引：用於查詢特定藥品的使用記錄
CREATE INDEX IF NOT EXISTS idx_include_med_id 
ON INCLUDE(med_id);

-- ============================================================
-- 索引建立完成
-- ============================================================
-- 可以使用以下 SQL 查詢檢查已建立的索引：
-- 
-- SELECT 
--     schemaname,
--     tablename,
--     indexname,
--     indexdef
-- FROM pg_indexes
-- WHERE schemaname = 'public'
-- ORDER BY tablename, indexname;
-- ============================================================

