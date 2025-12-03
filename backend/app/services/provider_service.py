# services/provider_service.py
import hashlib
from typing import Optional
from datetime import date, time
from fastapi import HTTPException
import psycopg2

from ..repositories import (
    ProviderRepository,
    SessionRepository,
    AppointmentRepository,
    EncounterRepository,
    DiagnosisRepository,
    PrescriptionRepository,
    LabResultRepository,
    PaymentRepository,
)


class ProviderService:
    """處理 Provider 相關的商業邏輯"""

    def __init__(self):
        self.provider_repo = ProviderRepository()
        self.session_repo = SessionRepository()
        self.appointment_repo = AppointmentRepository()
        self.encounter_repo = EncounterRepository()
        self.diagnosis_repo = DiagnosisRepository()
        self.prescription_repo = PrescriptionRepository()
        self.lab_result_repo = LabResultRepository()
        self.payment_repo = PaymentRepository()

    def register_provider(self, name: str, password: str, license_no: str, dept_id: int):
        """
        註冊醫師帳號：
        - 建立 USER（type = 'provider'）
        - 建立 PROVIDER
        回傳建立完成的 provider 資料（含 user_id）
        """
        # 簡單用 SHA-256 做 hash（專題作業等級夠用）
        hash_pwd = hashlib.sha256(password.encode("utf-8")).hexdigest()

        try:
            provider = self.provider_repo.create_provider_account(
                name=name,
                hash_pwd=hash_pwd,
                license_no=license_no,
                dept_id=dept_id,
            )
            return provider
        except psycopg2.IntegrityError as e:
            # PostgreSQL 完整性約束錯誤
            error_code = e.pgcode
            error_msg = str(e).lower()
            pgerror = e.pgerror.lower() if e.pgerror else ""
            
            # 23505 = unique_violation
            if error_code == '23505':
                # 檢查是哪個唯一約束違反
                if 'license_no' in error_msg or 'license_no' in pgerror or 'provider_license_no_key' in pgerror:
                    raise HTTPException(
                        status_code=400,
                        detail=f"執照號碼 '{license_no}' 已存在，請使用不同的執照號碼。"
                    ) from e
                else:
                    # 顯示完整的錯誤訊息以便調試
                    raise HTTPException(
                        status_code=400,
                        detail=f"資料唯一性約束違反：{e.pgerror or str(e)}"
                    ) from e
            # 23503 = foreign_key_violation
            elif error_code == '23503':
                if 'dept_id' in error_msg or 'dept_id' in pgerror or 'department' in pgerror or 'provider_dept_id_fkey' in pgerror:
                    raise HTTPException(
                        status_code=400,
                        detail=f"科別 ID {dept_id} 不存在，請確認科別 ID 是否正確。"
                    ) from e
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"外鍵約束違反：{e.pgerror or str(e)}"
                    ) from e
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"資料完整性錯誤（錯誤代碼：{error_code}）：{e.pgerror or str(e)}"
                ) from e
        except Exception as e:
            # 其他錯誤
            raise HTTPException(
                status_code=400,
                detail=f"無法建立醫師帳號：{str(e)}。請檢查輸入資料。"
            ) from e

    def get_provider_profile(self, provider_id: int):
        """取得醫師基本資料"""
        row = self.provider_repo.get_provider_profile(provider_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Provider not found")
        return row

    def login_provider(self, license_no: str, password: str):
        """醫師登入驗證"""
        hash_pwd = hashlib.sha256(password.encode("utf-8")).hexdigest()
        row = self.provider_repo.authenticate_provider_by_license(
            license_no=license_no,
            hash_pwd=hash_pwd,
        )
        if row is None:
            raise HTTPException(status_code=401, detail="Invalid license_no or password")

        return {
            "user_id": row["user_id"],
            "name": row["name"],
            "dept_id": row["dept_id"],
            "license_no": row["license_no"],
        }

    def list_sessions(
        self,
        provider_id: int,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        status: Optional[int] = None,
    ):
        """列出醫師的門診時段"""
        return self.session_repo.list_clinic_sessions_for_provider(
            provider_user_id=provider_id,
            from_date=from_date,
            to_date=to_date,
            status=status,
        )

    def create_session(
        self,
        provider_id: int,
        date_: date,
        start_time_: time,
        end_time_: time,
        capacity: int,
    ):
        """醫師新增門診時段"""
        if capacity <= 0:
            raise HTTPException(status_code=400, detail="Capacity must be positive")

        # 驗證時間：結束時間不可早於開始時間，且至少需相隔一小時
        start_minutes = start_time_.hour * 60 + start_time_.minute
        end_minutes = end_time_.hour * 60 + end_time_.minute
        if end_minutes <= start_minutes:
            raise HTTPException(
                status_code=400,
                detail="結束時間必須晚於開診時間",
            )
        if end_minutes - start_minutes < 60:
            raise HTTPException(
                status_code=400,
                detail="門診時間至少需為一小時",
            )

        session = self.session_repo.create_clinic_session(
            provider_user_id=provider_id,
            date_=date_,
            start_time_=start_time_,
            end_time_=end_time_,
            capacity=capacity,
        )
        return session

    def update_session(
        self,
        provider_id: int,
        session_id: int,
        date_: date,
        start_time_: time,
        end_time_: time,
        capacity: int,
        status: int,
    ):
        """醫師編輯門診時段"""
        if capacity <= 0:
            raise HTTPException(status_code=400, detail="Capacity must be positive")
        if status is None:
            raise HTTPException(status_code=400, detail="status is required for update")

        # 驗證時間：結束時間不可早於開始時間，且至少需相隔一小時
        start_minutes = start_time_.hour * 60 + start_time_.minute
        end_minutes = end_time_.hour * 60 + end_time_.minute
        if end_minutes <= start_minutes:
            raise HTTPException(
                status_code=400,
                detail="結束時間必須晚於開診時間",
            )
        if end_minutes - start_minutes < 60:
            raise HTTPException(
                status_code=400,
                detail="門診時間至少需為一小時",
            )

        row = self.session_repo.update_clinic_session(
            provider_user_id=provider_id,
            session_id=session_id,
            date_=date_,
            start_time_=start_time_,
            end_time_=end_time_,
            capacity=capacity,
            status=status,
        )
        if row is None:
            raise HTTPException(
                status_code=404, detail="Session not found or not owned by provider"
            )
        return row

    def cancel_session(self, provider_id: int, session_id: int):
        """醫師取消門診（將 status 設為 0 = 停診）"""
        ok = self.session_repo.cancel_clinic_session(provider_id, session_id, cancel_status=0)
        if not ok:
            raise HTTPException(
                status_code=404, detail="Session not found or not owned by provider"
            )
        return {"success": True}

    def update_expired_sessions(self, provider_id: int = None):
        """
        更新所有已過期的門診時段狀態為停診（status = 0）。
        如果提供 provider_id，只更新該醫師的門診時段。
        """
        updated_count = self.session_repo.update_expired_sessions(provider_id)
        return {"success": True, "updated_count": updated_count}

    def list_appointments(self, provider_id: int, session_id: int):
        """列出某個門診時段的掛號清單"""
        return self.appointment_repo.list_appointments_for_session(provider_id, session_id)

    def update_appointment_status(self, provider_id: int, appt_id: int, new_status: int):
        """醫師更新掛號狀態"""
        self.appointment_repo.update_appointment_status(provider_id, appt_id, new_status)
        return {"success": True, "appt_id": appt_id, "new_status": new_status}

    def get_encounter(self, provider_id: int, appt_id: int):
        """取得就診紀錄"""
        row = self.encounter_repo.get_encounter_by_appt(provider_id, appt_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Encounter not found")
        return row

    def get_appointment_patient_id(self, appt_id: int):
        """根據 appt_id 取得 patient_id"""
        appointment = self.appointment_repo.get_appointment_by_id(appt_id)
        if appointment is None:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return {"patient_id": appointment["patient_id"]}

    def upsert_encounter(
        self,
        provider_id: int,
        appt_id: int,
        status: int,
        chief_complaint: Optional[str] = None,
        subjective: Optional[str] = None,
        assessment: Optional[str] = None,
        plan: Optional[str] = None,
    ):
        """
        新增或更新就診紀錄
        注意：status = 1 為草稿，status = 2 為已定稿（不可再編輯）
        - 檢查門診時間是否在範圍內（僅在創建新 encounter 時檢查）
        """
        from ..repositories import SessionRepository
        
        # 檢查是否已定稿 - 如果已定稿，完全禁止編輯（包括內容和狀態）
        existing = self.encounter_repo.get_encounter_by_appt(provider_id, appt_id)
        if existing and existing.get("status") == 2:
            raise HTTPException(
                status_code=403,
                detail="Cannot modify finalized encounter"
            )
        
        # 如果不存在 encounter，則為創建新 encounter，需要檢查門診時間
        if existing is None:
            # 獲取 appointment 的 session_id
            appointment = self.appointment_repo.get_appointment_by_id(appt_id)
            if appointment is None:
                raise HTTPException(
                    status_code=404,
                    detail="Appointment not found"
                )
            
            session_id = appointment["session_id"]
            
            # 檢查門診時間是否在範圍內
            is_valid, session_info = SessionRepository.is_session_time_valid(session_id)
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail="只能在門診時間內建立就診記錄"
                )

        return self.encounter_repo.upsert_encounter(
            provider_user_id=provider_id,
            appt_id=appt_id,
            status=status,
            chief_complaint=chief_complaint,
            subjective=subjective,
            assessment=assessment,
            plan=plan,
        )

    def list_diagnoses(self, enct_id: int):
        """列出就診紀錄的所有診斷"""
        return self.diagnosis_repo.list_diagnoses_for_encounter(enct_id)

    def upsert_diagnosis(self, enct_id: int, code_icd: str, is_primary: bool):
        """新增或更新診斷"""
        import psycopg2
        try:
            self.diagnosis_repo.upsert_diagnosis(enct_id, code_icd, is_primary)
            return self.diagnosis_repo.list_diagnoses_for_encounter(enct_id)
        except psycopg2.IntegrityError as e:
            error_code = e.pgcode
            error_msg = str(e).lower()
            pgerror = e.pgerror.lower() if e.pgerror else ""
            
            # 23503 = foreign_key_violation
            if error_code == '23503':
                if 'enct_id' in error_msg or 'enct_id' in pgerror or 'encounter' in pgerror:
                    raise HTTPException(
                        status_code=400,
                        detail=f"就診記錄 (enct_id={enct_id}) 不存在"
                    ) from e
                elif 'code_icd' in error_msg or 'code_icd' in pgerror or 'disease' in pgerror:
                    raise HTTPException(
                        status_code=400,
                        detail=f"疾病代碼 '{code_icd}' 不存在於 DISEASE 表中"
                    ) from e
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"外鍵約束違反：{e.pgerror or str(e)}"
                    ) from e
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"無法新增診斷：{e.pgerror or str(e)}"
                ) from e
        except Exception as e:
            # 其他錯誤（包括自定義的驗證錯誤）
            raise HTTPException(
                status_code=400,
                detail=f"無法新增診斷：{str(e)}"
            ) from e

    def set_primary_diagnosis(self, enct_id: int, code_icd: str):
        """設定主要診斷"""
        try:
            self.diagnosis_repo.set_primary_diagnosis(enct_id, code_icd)
        except Exception as e:
            if "Diagnosis not found" in str(e):
                raise HTTPException(
                    status_code=404,
                    detail="Diagnosis not found for this encounter"
                )
            raise HTTPException(
                status_code=500,
                detail=f"Error setting primary diagnosis: {str(e)}"
            ) from e
        return self.diagnosis_repo.list_diagnoses_for_encounter(enct_id)

    def search_diseases(self, query: str = None, limit: int = 50):
        """搜尋疾病（ICD 代碼和描述）"""
        return self.diagnosis_repo.search_diseases(query, limit)

    def search_medications(self, query: str = None, limit: int = 50):
        """搜尋藥品（med_id 和 name）"""
        return self.prescription_repo.search_medications(query, limit)

    def get_prescription(self, enct_id: int):
        """取得處方箋，如果不存在則返回 None（與 get_payment 行為一致）"""
        rx = self.prescription_repo.get_prescription_for_encounter(enct_id)
        # 如果處方不存在，返回 None 而不是拋出 404
        # 前端已經用 .catch(() => null) 處理，但為了保持一致性，這裡也返回 None
        return rx

    def upsert_prescription(self, enct_id: int, status: int, items: list):
        """新增或更新處方箋"""
        header = self.prescription_repo.upsert_prescription_for_encounter(enct_id, status)
        rx_id = header["rx_id"]
        items_dicts = [item if isinstance(item, dict) else item.dict() for item in items]
        self.prescription_repo.replace_prescription_items(rx_id, items_dicts)
        return self.prescription_repo.get_prescription_for_encounter(enct_id)

    def list_encounters_for_patient_by_provider(self, provider_id: int, patient_id: int):
        """醫師查詢某位病患在自己這裡的所有就診紀錄"""
        return self.encounter_repo.list_encounters_for_patient_by_provider(provider_id, patient_id)

    def list_all_encounters_for_patient(self, patient_id: int):
        """醫師查詢某位病患的所有就診紀錄（不限醫師、科別）"""
        return self.encounter_repo.list_encounters_for_patient(patient_id, provider_id=None)

    def list_all_diagnoses_for_patient(self, patient_id: int):
        """醫師查詢某位病患的所有診斷（不限醫師、科別）"""
        return self.diagnosis_repo.list_diagnoses_for_patient(patient_id)

    def list_all_lab_results_for_patient(self, patient_id: int):
        """醫師查詢某位病患的所有檢驗結果（不限醫師、科別）"""
        return self.lab_result_repo.list_lab_results_for_patient(patient_id)

    def list_lab_results(self, enct_id: int):
        """列出某次就診的所有檢驗結果"""
        return self.lab_result_repo.list_lab_results_for_encounter(enct_id)

    def add_lab_result(
        self,
        provider_id: int,
        enct_id: int,
        loinc_code: Optional[str],
        item_name: str,
        value: Optional[str],
        unit: Optional[str],
        ref_low: Optional[str],
        ref_high: Optional[str],
        abnormal_flag: Optional[str],
        reported_at: Optional[str],
    ):
        """
        新增檢驗結果：
        - abnormal_flag: 'H' (高), 'L' (低), 'N' (正常), None
        """
        # 驗證 abnormal_flag 值
        if abnormal_flag is not None and abnormal_flag not in ('H', 'L', 'N'):
            raise HTTPException(
                status_code=400,
                detail="abnormal_flag must be 'H', 'L', 'N', or None"
            )

        return self.lab_result_repo.add_lab_result(
            enct_id=enct_id,
            loinc_code=loinc_code,
            item_name=item_name,
            value=value,
            unit=unit,
            ref_low=ref_low,
            ref_high=ref_high,
            abnormal_flag=abnormal_flag,
            reported_at=reported_at,
        )

    def get_payment(self, enct_id: int):
        """取得某次就診的繳費資訊"""
        payment = self.payment_repo.get_payment_for_encounter(enct_id)
        if payment is None:
            raise HTTPException(status_code=404, detail="Payment not found")
        return payment

    def upsert_payment(self, enct_id: int, amount: float, method: str, invoice_no: Optional[str]):
        """
        建立或更新繳費資料：
        - 系統根據醫療服務與藥品清單自動計算費用
        - 或由醫師/櫃台人員手動輸入
        - method: 'cash' (現金), 'card' (信用卡), 'insurer' (保險)
        """
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")

        # 驗證 method 值
        if method not in ('cash', 'card', 'insurer'):
            raise HTTPException(
                status_code=400,
                detail="method must be 'cash', 'card', or 'insurer'"
            )

        return self.payment_repo.upsert_payment_for_encounter(
            enct_id=enct_id,
            amount=amount,
            method=method,
            invoice_no=invoice_no,
        )

