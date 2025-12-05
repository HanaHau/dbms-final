# routers/patient_router.py
from fastapi import APIRouter, HTTPException, Query
from datetime import date
from typing import Optional
from pydantic import BaseModel

from ..services.shared import AppointmentService, SessionService
from ..services.patient_history_service import PatientHistoryService
from ..services.patient_service import PatientService

router = APIRouter()
appointment_service = AppointmentService()
session_service = SessionService()
history_service = PatientHistoryService()
patient_service = PatientService()


# ---------- Pydantic Models ----------

class PatientRegisterRequest(BaseModel):
    name: str
    password: str
    national_id: str  # 身分證字號
    birth_date: date
    sex: str  # 'M', 'F', 'O'
    phone: str


class PatientLoginRequest(BaseModel):
    national_id: str  # 身分證字號
    password: str


class PatientLoginResponse(BaseModel):
    user_id: int
    name: str
    national_id: str
    birth_date: date
    sex: str
    phone: str


class AppointmentCreateRequest(BaseModel):
    session_id: int


class AppointmentRescheduleRequest(BaseModel):
    new_session_id: int


class PaymentUpdateRequest(BaseModel):
    method: str  # 付款方式：'cash' (現金), 'card' (信用卡), 'insurer' (保險)
    invoice_no: Optional[str] = None


# ---------------------------
# Patient APIs
# ---------------------------

@router.post("/register")
def api_register_patient(body: PatientRegisterRequest):
    """
    註冊病患帳號：
    - 建立 USER（type = 'patient'）
    - 建立 PATIENT（包含身分證字號、生日、電話）
    回傳建立完成的 patient 資料（含 user_id）
    """
    return patient_service.register_patient(
        name=body.name,
        password=body.password,
        national_id=body.national_id,
        birth_date=body.birth_date,
        sex=body.sex,
        phone=body.phone,
    )


@router.post("/login", response_model=PatientLoginResponse)
def api_login_patient(body: PatientLoginRequest):
    """病患登入"""
    result = patient_service.login_patient(
        national_id=body.national_id,
        password=body.password,
    )
    return PatientLoginResponse(**result)


@router.get("/{patient_id}/profile")
def api_get_patient_profile(patient_id: int):
    """取得病患基本資料"""
    return patient_service.get_patient_profile(patient_id)


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
    """
    # 獲取掛號資訊並驗證權限
    from ..repositories import AppointmentRepository
    appointment = AppointmentRepository.get_appointment_by_id(appt_id)
    
    if appointment is None or appointment["patient_id"] != patient_id:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found or patient_id does not match"
        )
    
    old_session_id = appointment["session_id"]
    
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


@router.get("/payments")
def api_list_payments(patient_id: int = Query(...)):
    """
    列出某位病人的所有繳費記錄。
    包含：繳費 ID、就診 ID、金額、付款方式、發票號碼等。
    """
    from ..repositories import PaymentRepository
    payment_repo = PaymentRepository()
    return payment_repo.list_payments_for_patient(patient_id)


@router.post("/payments/{payment_id}/pay")
def api_pay_online(
    payment_id: int,
    patient_id: int = Query(...),
    body: PaymentUpdateRequest = ...,
):
    """
    線上繳費（更新付款方式與發票號碼）：
    - 驗證 payment 是否屬於該病人
    - 更新付款方式與發票號碼
    注意：實際金額由系統計算，此處只更新付款資訊
    """
    from ..repositories import PaymentRepository
    from ..pg_base import get_pg_conn
    from psycopg2.extras import RealDictCursor
    
    payment_repo = PaymentRepository()
    
    # 獲取 payment 資訊
    payment = payment_repo.get_payment_for_encounter(payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    enct_id = payment["enct_id"]
    
    # 驗證 encounter 是否屬於該病人（使用單次查詢）
    conn = get_pg_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT 1
                FROM ENCOUNTER e
                JOIN APPOINTMENT a ON e.appt_id = a.appt_id
                WHERE e.enct_id = %s AND a.patient_id = %s;
                """,
                (enct_id, patient_id),
            )
            if cur.fetchone() is None:
                raise HTTPException(
                    status_code=403,
                    detail="Payment does not belong to this patient"
                )
    finally:
        conn.close()
    
    # 更新付款資訊（保持原金額）
    return payment_repo.upsert_payment_for_encounter(
        enct_id=enct_id,
        amount=payment["amount"],
        method=body.method,
        invoice_no=body.invoice_no,
    )

