# services/provider_service.py
import hashlib
from typing import Optional
from datetime import date, time
from fastapi import HTTPException

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
        except Exception as e:
            # 這裡可以再細分錯誤型別，先簡單處理常見情況
            # 例如 license_no UNIQUE 衝突
            raise HTTPException(
                status_code=400, detail="Cannot create provider, please check license_no / dept_id."
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
        """
        # 檢查是否已定稿 - 如果已定稿，完全禁止編輯（包括內容和狀態）
        existing = self.encounter_repo.get_encounter_by_appt(provider_id, appt_id)
        if existing and existing.get("status") == 2:
            raise HTTPException(
                status_code=403,
                detail="Cannot modify finalized encounter"
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
        self.diagnosis_repo.upsert_diagnosis(enct_id, code_icd, is_primary)
        return self.diagnosis_repo.list_diagnoses_for_encounter(enct_id)

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

    def get_prescription(self, enct_id: int):
        """取得處方箋"""
        rx = self.prescription_repo.get_prescription_for_encounter(enct_id)
        if rx is None:
            raise HTTPException(status_code=404, detail="Prescription not found")
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

