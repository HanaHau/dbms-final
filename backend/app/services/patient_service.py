# services/patient_service.py
import hashlib
from datetime import date
from typing import Optional
from fastapi import HTTPException

from ..repositories import PatientRepository


class PatientService:
    """處理 Patient 相關的商業邏輯"""

    def __init__(self):
        self.patient_repo = PatientRepository()

    def register_patient(
        self, name: str, password: str, national_id: str, birth_date: date, sex: str, phone: str
    ):
        """
        註冊病患帳號：
        - 建立 USER（type = 'patient'）
        - 建立 PATIENT
        回傳建立完成的 patient 資料（含 user_id）
        """
        # 簡單用 SHA-256 做 hash（專題作業等級夠用）
        hash_pwd = hashlib.sha256(password.encode("utf-8")).hexdigest()

        try:
            patient = self.patient_repo.create_patient_account(
                name=name,
                hash_pwd=hash_pwd,
                national_id=national_id,
                birth_date=birth_date,
                sex=sex,
                phone=phone,
            )
            return patient
        except Exception as e:
            # 這裡可以再細分錯誤型別，先簡單處理常見情況
            # 例如 national_id UNIQUE 衝突
            raise HTTPException(
                status_code=400,
                detail="Cannot create patient account, please check national_id (身分證字號可能重複).",
            ) from e

    def get_patient_profile(self, patient_id: int):
        """取得病患基本資料"""
        row = self.patient_repo.get_patient_profile(patient_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Patient not found")
        return row

    def login_patient(self, national_id: str, password: str):
        """病患登入驗證"""
        hash_pwd = hashlib.sha256(password.encode("utf-8")).hexdigest()
        row = self.patient_repo.authenticate_patient_by_national_id(
            national_id=national_id,
            hash_pwd=hash_pwd,
        )
        if row is None:
            raise HTTPException(
                status_code=401, detail="Invalid national_id or password"
            )

        return {
            "user_id": row["user_id"],
            "name": row["name"],
            "national_id": row["national_id"],
            "birth_date": row["birth_date"],
            "sex": row["sex"],
            "phone": row["phone"],
        }
