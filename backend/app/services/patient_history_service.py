# services/patient_history_service.py
from ..repositories import (
    EncounterRepository,
    PrescriptionRepository,
    LabResultRepository,
    PaymentRepository,
    DiagnosisRepository,
)


class PatientHistoryService:
    """處理病人歷史記錄相關的服務"""

    def __init__(self):
        self.encounter_repo = EncounterRepository()
        self.prescription_repo = PrescriptionRepository()
        self.lab_result_repo = LabResultRepository()
        self.payment_repo = PaymentRepository()
        self.diagnosis_repo = DiagnosisRepository()

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

    def get_all_diagnoses(self, patient_id: int):
        """
        取得某位病人的所有診斷。
        包含：就診 ID、ICD 代碼、疾病描述、是否主要診斷等。
        """
        return self.diagnosis_repo.list_diagnoses_for_patient(patient_id)

    def get_patient_history(self, patient_id: int):
        """
        取得某位病人的完整歷史記錄（優化版本）。
        使用單次走訪策略：先取得就診列表，然後批量查詢所有相關資料。
        包含：所有就診記錄、處方箋、檢驗結果、繳費記錄、診斷。
        """
        # 第一步：取得所有就診記錄（輕量查詢，只 JOIN 必要的表）
        encounters = self.get_all_encounters(patient_id)
        
        # 如果沒有就診記錄，直接返回空結果
        if not encounters:
            return {
                "encounters": [],
                "prescriptions": [],
                "lab_results": [],
                "payments": [],
                "diagnoses": [],
            }
        
        # 提取所有 enct_id
        enct_ids = [encounter["enct_id"] for encounter in encounters]
        
        # 第二步：使用批量查詢方法，一次性查詢所有相關資料
        # 這些查詢都使用 enct_id IN (...) 或 ANY(%s)，避免重複 JOIN APPOINTMENT 表
        diagnoses = self.diagnosis_repo.list_diagnoses_for_encounters(enct_ids)
        prescriptions = self.prescription_repo.list_prescriptions_for_encounters(enct_ids)
        lab_results = self.lab_result_repo.list_lab_results_for_encounters(enct_ids)
        payments = self.payment_repo.list_payments_for_encounters(enct_ids)
        
        return {
            "encounters": encounters,
            "prescriptions": prescriptions,
            "lab_results": lab_results,
            "payments": payments,
            "diagnoses": diagnoses,
        }

