# services/patient_history_service.py
from ..repositories import (
    EncounterRepository,
    PrescriptionRepository,
    LabResultRepository,
    PaymentRepository,
)


class PatientHistoryService:
    """處理病人歷史記錄相關的服務"""

    def __init__(self):
        self.encounter_repo = EncounterRepository()
        self.prescription_repo = PrescriptionRepository()
        self.lab_result_repo = LabResultRepository()
        self.payment_repo = PaymentRepository()

    def get_all_encounters(self, patient_id: int):
        """
        取得某位病人的所有就診記錄。
        包含：就診 ID、掛號資訊、門診時段資訊、醫師資訊等。
        """
        return self.encounter_repo.list_encounters_for_patient(patient_id)

    def get_all_prescriptions(self, patient_id: int):
        """
        取得某位病人的所有處方箋。
        包含：處方 ID、就診 ID、用藥明細等。
        """
        return self.prescription_repo.list_prescriptions_for_patient(patient_id)

    def get_all_lab_results(self, patient_id: int):
        """
        取得某位病人的所有檢驗結果。
        包含：檢驗 ID、就診 ID、檢驗項目、數值等。
        """
        return self.lab_result_repo.list_lab_results_for_patient(patient_id)

    def get_all_payments(self, patient_id: int):
        """
        取得某位病人的所有繳費記錄。
        包含：繳費 ID、就診 ID、金額、付款方式、發票號碼等。
        """
        return self.payment_repo.list_payments_for_patient(patient_id)

    def get_patient_history(self, patient_id: int):
        """
        取得某位病人的完整歷史記錄。
        包含：所有就診記錄、處方箋、檢驗結果、繳費記錄。
        """
        return {
            "encounters": self.get_all_encounters(patient_id),
            "prescriptions": self.get_all_prescriptions(patient_id),
            "lab_results": self.get_all_lab_results(patient_id),
            "payments": self.get_all_payments(patient_id),
        }

