# services/shared/appointment_service.py
from fastapi import HTTPException

from ...repositories import AppointmentRepository


class AppointmentService:
    """共享的 Appointment 服務，提供通用的掛號管理功能"""

    def __init__(self):
        self.appointment_repo = AppointmentRepository()

    def create_appointment(self, patient_id: int, session_id: int):
        """
        建立掛號：
        - 使用 transaction + FOR UPDATE 避免併行衝突
        - slot_seq = 已掛號人數 + 1
        - 寫入 APPOINTMENT_STATUS_HISTORY
        """
        try:
            appt = self.appointment_repo.create_appointment(patient_id, session_id)
            if appt is None:
                raise HTTPException(status_code=400, detail="Failed to create appointment")
            return appt
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error creating appointment: {str(e)}") from e

    def cancel_appointment(self, appt_id: int, patient_id: int):
        """
        取消掛號：
        - 驗證 patient_id 是否匹配
        - 更新狀態為「已取消」
        - 寫入 APPOINTMENT_STATUS_HISTORY
        """
        result = self.appointment_repo.cancel_appointment(appt_id, patient_id)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Appointment not found or patient_id does not match"
            )
        return result

    def modify_appointment(
        self, appt_id: int, old_session_id: int, new_session_id: int
    ):
        """
        修改掛號（更換門診時段）：
        - 使用固定鎖序避免死鎖
        - 更新 session_id 和 slot_seq
        - 寫入 APPOINTMENT_STATUS_HISTORY
        """
        try:
            appt = self.appointment_repo.modify_appointment(
                appt_id, old_session_id, new_session_id
            )
            if appt is None:
                raise HTTPException(
                    status_code=404,
                    detail="Appointment not found or session_id does not match"
                )
            return appt
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=500, detail=f"Error modifying appointment: {str(e)}"
            ) from e

    def list_appointments_for_patient(self, patient_id: int):
        """
        列出某位病人的所有掛號。
        包含：掛號 ID、門診時段資訊、slot_seq、目前掛號狀態。
        """
        return self.appointment_repo.list_appointments_for_patient(patient_id)

    def checkin_appointment(self, patient_id: int, appt_id: int):
        """
        病人報到（checkin）：
        - 驗證 patient_id 是否匹配
        - 更新狀態為「已報到」（假設狀態 3 為「已報到」）
        - 寫入 APPOINTMENT_STATUS_HISTORY
        """
        result = self.appointment_repo.update_appointment_status_by_patient(
            patient_id, appt_id, 3  # 狀態 3 = 已報到
        )
        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Appointment not found or patient_id does not match"
            )
        return result

