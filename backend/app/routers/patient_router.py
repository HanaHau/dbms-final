# routers/patient_router.py
from fastapi import APIRouter, HTTPException, Query
from datetime import date
from typing import Optional
from pydantic import BaseModel

from ..services.shared import AppointmentService, SessionService
from ..services.patient_history_service import PatientHistoryService

router = APIRouter()
appointment_service = AppointmentService()
session_service = SessionService()
history_service = PatientHistoryService()


# ---------- Pydantic Models ----------

class AppointmentCreateRequest(BaseModel):
    session_id: int


class AppointmentRescheduleRequest(BaseModel):
    new_session_id: int


# ---------------------------
# Patient APIs
# ---------------------------

@router.get("/sessions")
def api_list_sessions(
    dept_id: Optional[int] = Query(None),
    provider_id: Optional[int] = Query(None),
    date_: Optional[date] = Query(None, alias="date"),
):
    """
    列出可預約的門診時段。
    可根據科別、醫師、日期過濾。
    """
    return session_service.search_sessions(
        dept_id=dept_id,
        provider_id=provider_id,
        date_=date_,
    )


@router.get("/appointments")
def api_list_appointments(patient_id: int = Query(...)):
    """
    列出某位病人的所有掛號。
    包含：掛號 ID、門診時段資訊、slot_seq、目前掛號狀態。
    """
    return appointment_service.list_appointments_for_patient(patient_id)


@router.post("/appointments")
def api_create_appointment(
    patient_id: int = Query(...),
    body: AppointmentCreateRequest = ...,
):
    """
    建立掛號：
    - 使用 transaction + FOR UPDATE 避免併行衝突
    - slot_seq = 已掛號人數 + 1
    - 寫入 APPOINTMENT_STATUS_HISTORY
    """
    return appointment_service.create_appointment(
        patient_id=patient_id,
        session_id=body.session_id,
    )


@router.delete("/appointments/{appt_id}")
def api_cancel_appointment(
    appt_id: int,
    patient_id: int = Query(...),
):
    """
    取消掛號：
    - 驗證 patient_id 是否匹配
    - 更新狀態為「已取消」
    - 寫入 APPOINTMENT_STATUS_HISTORY
    """
    return appointment_service.cancel_appointment(
        appt_id=appt_id,
        patient_id=patient_id,
    )


@router.patch("/appointments/{appt_id}/reschedule")
def api_reschedule_appointment(
    appt_id: int,
    patient_id: int = Query(...),
    body: AppointmentRescheduleRequest = ...,
):
    """
    修改掛號（更換門診時段）：
    - 使用固定鎖序避免死鎖
    - 更新 session_id 和 slot_seq
    - 寫入 APPOINTMENT_STATUS_HISTORY
    
    注意：需要先查詢 appointment 獲取 old_session_id
    """
    # 先查詢 appointment 獲取 old_session_id
    appointments = appointment_service.list_appointments_for_patient(patient_id)
    target_appt = None
    for appt in appointments:
        if appt["appt_id"] == appt_id:
            target_appt = appt
            break
    
    if target_appt is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found or patient_id does not match"
        )
    
    old_session_id = target_appt["session_id"]
    
    return appointment_service.modify_appointment(
        appt_id=appt_id,
        old_session_id=old_session_id,
        new_session_id=body.new_session_id,
    )


@router.post("/appointments/{appt_id}/checkin")
def api_checkin_appointment(
    appt_id: int,
    patient_id: int = Query(...),
):
    """
    病人報到（checkin）：
    - 驗證 patient_id 是否匹配
    - 更新狀態為「已報到」
    - 寫入 APPOINTMENT_STATUS_HISTORY
    """
    return appointment_service.checkin_appointment(
        patient_id=patient_id,
        appt_id=appt_id,
    )


@router.get("/history")
def api_get_patient_history(patient_id: int = Query(...)):
    """
    取得某位病人的完整歷史記錄。
    包含：所有就診記錄、處方箋、檢驗結果、繳費記錄。
    """
    return history_service.get_patient_history(patient_id)

