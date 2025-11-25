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
        """新增或更新就診紀錄"""
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
        self.diagnosis_repo.set_primary_diagnosis(enct_id, code_icd)
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

