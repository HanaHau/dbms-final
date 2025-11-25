# routers/provider_router.py
from fastapi import APIRouter, Query
from datetime import date, time
from typing import Optional, List
from pydantic import BaseModel

from ..services import ProviderService

router = APIRouter()
service = ProviderService()


# ---------- Pydantic Models ----------

class ProviderRegisterRequest(BaseModel):
    name: str
    password: str
    license_no: str
    dept_id: int


class ProviderLoginRequest(BaseModel):
    license_no: str
    password: str


class ProviderLoginResponse(BaseModel):
    user_id: int
    name: str
    dept_id: int
    license_no: str


class SessionCreateUpdate(BaseModel):
    date: date
    start_time: time
    end_time: time
    capacity: int
    status: Optional[int] = 1  # 新增時可忽略，更新時可用


class EncounterUpsert(BaseModel):
    status: int
    chief_complaint: Optional[str] = None
    subjective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None


class DiagnosisUpsert(BaseModel):
    is_primary: bool = False


class PrimaryDiagnosisBody(BaseModel):
    code_icd: str


class PrescriptionItem(BaseModel):
    med_id: int
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    days: int
    quantity: float


class PrescriptionUpsert(BaseModel):
    status: int
    items: List[PrescriptionItem]


class LabResultCreate(BaseModel):
    loinc_code: Optional[str] = None
    item_name: str
    value: Optional[str] = None
    unit: Optional[str] = None
    ref_low: Optional[str] = None
    ref_high: Optional[str] = None
    abnormal_flag: Optional[str] = None  # 'H' (高), 'L' (低), 'N' (正常)
    reported_at: Optional[str] = None  # ISO format or None for NOW()


class PaymentCreate(BaseModel):
    amount: float
    method: str  # 'cash' (現金), 'card' (信用卡), 'insurer' (保險)
    invoice_no: Optional[str] = None


# ---------------------------
# Provider APIs
# ---------------------------

@router.post("/register")
def api_register_provider(body: ProviderRegisterRequest):
    """
    註冊醫師帳號：
    - 建立 USER（type = 'provider'）
    - 建立 PROVIDER
    回傳建立完成的 provider 資料（含 user_id）
    """
    return service.register_provider(
        name=body.name,
        password=body.password,
        license_no=body.license_no,
        dept_id=body.dept_id,
    )


@router.get("/{provider_id}/profile")
def api_get_provider_profile(provider_id: int):
    """取得醫師基本資料"""
    return service.get_provider_profile(provider_id)


@router.post("/login", response_model=ProviderLoginResponse)
def api_login_provider(body: ProviderLoginRequest):
    """醫師登入"""
    result = service.login_provider(
        license_no=body.license_no,
        password=body.password,
    )
    return ProviderLoginResponse(**result)


@router.get("/{provider_id}/sessions")
def api_list_sessions(
    provider_id: int,
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    status: Optional[int] = Query(None),
):
    """列出醫師的門診時段"""
    return service.list_sessions(
        provider_id=provider_id,
        from_date=from_date,
        to_date=to_date,
        status=status,
    )


@router.post("/{provider_id}/sessions")
def api_create_session(provider_id: int, body: SessionCreateUpdate):
    """
    醫師新增門診時段。
    """
    return service.create_session(
        provider_id=provider_id,
        date_=body.date,
        start_time_=body.start_time,
        end_time_=body.end_time,
        capacity=body.capacity,
    )


@router.put("/{provider_id}/sessions/{session_id}")
def api_update_session(provider_id: int, session_id: int, body: SessionCreateUpdate):
    """
    醫師編輯門診時段（日期、時間、人數上限、狀態）。
    """
    return service.update_session(
        provider_id=provider_id,
        session_id=session_id,
        date_=body.date,
        start_time_=body.start_time,
        end_time_=body.end_time,
        capacity=body.capacity,
        status=body.status,
    )


@router.post("/{provider_id}/sessions/{session_id}/cancel")
def api_cancel_session(provider_id: int, session_id: int):
    """
    醫師取消門診（將 status 設為 0 = 停診）。
    """
    return service.cancel_session(provider_id, session_id)


@router.get("/{provider_id}/sessions/{session_id}/appointments")
def api_list_appointments(provider_id: int, session_id: int):
    """列出某個門診時段的掛號清單"""
    return service.list_appointments(provider_id, session_id)


@router.get("/{provider_id}/appointments/{appt_id}/encounter")
def api_get_encounter(provider_id: int, appt_id: int):
    """取得就診紀錄"""
    return service.get_encounter(provider_id, appt_id)


@router.put("/{provider_id}/appointments/{appt_id}/encounter")
def api_upsert_encounter(provider_id: int, appt_id: int, body: EncounterUpsert):
    """新增或更新就診紀錄"""
    return service.upsert_encounter(
        provider_id=provider_id,
        appt_id=appt_id,
        status=body.status,
        chief_complaint=body.chief_complaint,
        subjective=body.subjective,
        assessment=body.assessment,
        plan=body.plan,
    )


@router.get("/{provider_id}/encounters/{enct_id}/diagnoses")
def api_get_diagnoses(provider_id: int, enct_id: int):
    """列出就診紀錄的所有診斷"""
    return service.list_diagnoses(enct_id)


@router.put("/{provider_id}/encounters/{enct_id}/diagnoses/{code_icd}")
def api_upsert_dx(provider_id: int, enct_id: int, code_icd: str, body: DiagnosisUpsert):
    """新增或更新診斷"""
    return service.upsert_diagnosis(enct_id, code_icd, body.is_primary)


@router.post("/{provider_id}/encounters/{enct_id}/primary-diagnosis")
def api_set_primary_dx(provider_id: int, enct_id: int, body: PrimaryDiagnosisBody):
    """設定主要診斷"""
    return service.set_primary_diagnosis(enct_id, body.code_icd)


@router.get("/{provider_id}/encounters/{enct_id}/prescription")
def api_get_rx(provider_id: int, enct_id: int):
    """取得處方箋"""
    return service.get_prescription(enct_id)


@router.put("/{provider_id}/encounters/{enct_id}/prescription")
def api_upsert_rx(provider_id: int, enct_id: int, body: PrescriptionUpsert):
    """新增或更新處方箋"""
    return service.upsert_prescription(
        enct_id=enct_id,
        status=body.status,
        items=body.items,
    )


@router.get("/{provider_id}/encounters/{enct_id}/lab-results")
def api_get_lab_results(provider_id: int, enct_id: int):
    """取得某次就診的所有檢驗結果"""
    return service.list_lab_results(enct_id)


@router.post("/{provider_id}/encounters/{enct_id}/lab-results")
def api_add_lab_result(provider_id: int, enct_id: int, body: LabResultCreate):
    """新增檢驗結果"""
    return service.add_lab_result(
        provider_id=provider_id,
        enct_id=enct_id,
        loinc_code=body.loinc_code,
        item_name=body.item_name,
        value=body.value,
        unit=body.unit,
        ref_low=body.ref_low,
        ref_high=body.ref_high,
        abnormal_flag=body.abnormal_flag,
        reported_at=body.reported_at,
    )


@router.get("/{provider_id}/encounters/{enct_id}/payment")
def api_get_payment(provider_id: int, enct_id: int):
    """取得某次就診的繳費資訊"""
    return service.get_payment(enct_id)


@router.post("/{provider_id}/encounters/{enct_id}/payment")
def api_create_payment(provider_id: int, enct_id: int, body: PaymentCreate):
    """建立或更新繳費資料"""
    return service.upsert_payment(
        enct_id=enct_id,
        amount=body.amount,
        method=body.method,
        invoice_no=body.invoice_no,
    )

