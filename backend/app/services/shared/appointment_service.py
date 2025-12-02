from fastapi import HTTPException

from ...repositories import AppointmentRepository


class AppointmentService:
    """共享的 Appointment 服務，提供通用的掛號管理功能"""

    def __init__(self):
        self.appointment_repo = AppointmentRepository()

    def create_appointment(self, patient_id: int, session_id: int):
        """
        建立掛號：
        - 檢查是否已在該 session 重複掛號
        - 檢查 session 容量是否已滿
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
            import traceback
            error_msg = str(e)
            error_trace = traceback.format_exc()
            print(f"❌ 建立掛號錯誤:")
            print(f"   patient_id: {patient_id}, session_id: {session_id}")
            print(f"   錯誤訊息: {error_msg}")
            print(f"   錯誤堆疊:\n{error_trace}")
            
            if "already has an appointment" in error_msg or "無法重複預約" in error_msg:
                raise HTTPException(
                    status_code=409,
                    detail="無法重複預約同一門診"
                )
            elif "Session is full" in error_msg:
                raise HTTPException(
                    status_code=409,
                    detail="Session is full, no more appointments available"
                )
            elif "Session not found" in error_msg:
                raise HTTPException(status_code=404, detail="Session not found")
            elif "Session has ended" in error_msg or "cannot book appointment" in error_msg:
                raise HTTPException(
                    status_code=409,
                    detail="此門診時段已結束，無法預約"
                )
            elif "Session is cancelled" in error_msg or "cancelled" in error_msg.lower():
                raise HTTPException(
                    status_code=409,
                    detail="此門診時段已取消"
                )
            raise HTTPException(status_code=500, detail=f"Error creating appointment: {error_msg}") from e

    def cancel_appointment(self, appt_id: int, patient_id: int):
        """
        取消掛號：
        - 驗證 patient_id 是否匹配
        - 更新狀態為「已取消」
        - 寫入 APPOINTMENT_STATUS_HISTORY
        """
        try:
            result = self.appointment_repo.cancel_appointment(appt_id, patient_id)
            if result is None:
                raise HTTPException(
                    status_code=404,
                    detail="Appointment not found or patient_id does not match"
                )
            return result
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            import traceback
            error_msg = str(e)
            error_trace = traceback.format_exc()
            print(f"❌ 取消掛號錯誤:")
            print(f"   appt_id: {appt_id}, patient_id: {patient_id}")
            print(f"   錯誤訊息: {error_msg}")
            print(f"   錯誤堆疊:\n{error_trace}")
            raise HTTPException(
                status_code=500,
                detail=f"Error cancelling appointment: {error_msg}"
            ) from e

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
        - 更新狀態為「已報到」（狀態 2 = 已報到）
        - 寫入 APPOINTMENT_STATUS_HISTORY
        """
        result = self.appointment_repo.update_appointment_status_by_patient(
            patient_id, appt_id, 2  # 狀態 2 = 已報到
        )
        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Appointment not found or patient_id does not match"
            )
        return result
