# router_provider.py
from fastapi import APIRouter, HTTPException, Query
from datetime import date
from typing import Optional, List
from pydantic import BaseModel
import hashlib
from .pg_provider import (
    create_provider_account,
    get_provider_profile,
    list_clinic_sessions_for_provider,
    list_appointments_for_session,
    get_encounter_by_appt,
    upsert_encounter,
    list_diagnoses_for_encounter,
    upsert_diagnosis,
    set_primary_diagnosis,
    get_prescription_for_encounter,
    upsert_prescription_for_encounter,
    replace_prescription_items,
)

router = APIRouter()

# ---------------------------
# Pydantic Models
# ---------------------------

# router_provider.py
import hashlib
from datetime import date, time
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .pg_provider import (
    create_provider_account,
    authenticate_provider_by_license,
    get_provider_profile,
    list_clinic_sessions_for_provider,
    create_clinic_session,
    update_clinic_session,
    cancel_clinic_session,
    list_appointments_for_session,
    get_encounter_by_appt,
    upsert_encounter,
    list_diagnoses_for_encounter,
    upsert_diagnosis,
    set_primary_diagnosis,
    get_prescription_for_encounter,
    upsert_prescription_for_encounter,
    replace_prescription_items,
)

router = APIRouter()


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
    # 簡單用 SHA-256 做 hash（專題作業等級夠用）
    hash_pwd = hashlib.sha256(body.password.encode("utf-8")).hexdigest()

    try:
        provider = create_provider_account(
            name=body.name,
            hash_pwd=hash_pwd,
            license_no=body.license_no,
            dept_id=body.dept_id,
        )
    except Exception as e:
        # 這裡可以再細分錯誤型別，先簡單處理常見情況
        # 例如 license_no UNIQUE 衝突
        raise HTTPException(status_code=400, detail="Cannot create provider, please check license_no / dept_id.") from e

    return provider

@router.get("/{provider_id}/profile")
def api_get_provider_profile(provider_id: int):
    row = get_provider_profile(provider_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    return row

@router.post("/login", response_model=ProviderLoginResponse)
def api_login_provider(body: ProviderLoginRequest):
    hash_pwd = hashlib.sha256(body.password.encode("utf-8")).hexdigest()
    row = authenticate_provider_by_license(
        license_no=body.license_no,
        hash_pwd=hash_pwd,
    )
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid license_no or password")

    return ProviderLoginResponse(
        user_id=row["user_id"],
        name=row["name"],
        dept_id=row["dept_id"],
        license_no=row["license_no"],
    )

@router.get("/{provider_id}/sessions")
def api_list_sessions(
    provider_id: int,
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    status: Optional[int] = Query(None),
):
    return list_clinic_sessions_for_provider(
        provider_user_id=provider_id,
        from_date=from_date,
        to_date=to_date,
        status=status,
    )


@router.post("/{provider_id}/sessions")
def api_create_session(provider_id: int, body: SessionCreateUpdate):
    """
    醫師新增門診時段。
    """
    if body.capacity <= 0:
        raise HTTPException(status_code=400, detail="Capacity must be positive")

    session = create_clinic_session(
        provider_user_id=provider_id,
        date_=body.date,
        start_time_=body.start_time,
        end_time_=body.end_time,
        capacity=body.capacity,
    )
    return session


@router.put("/{provider_id}/sessions/{session_id}")
def api_update_session(provider_id: int, session_id: int, body: SessionCreateUpdate):
    """
    醫師編輯門診時段（日期、時間、人數上限、狀態）。
    """
    if body.capacity <= 0:
        raise HTTPException(status_code=400, detail="Capacity must be positive")
    if body.status is None:
        raise HTTPException(status_code=400, detail="status is required for update")

    row = update_clinic_session(
        provider_user_id=provider_id,
        session_id=session_id,
        date_=body.date,
        start_time_=body.start_time,
        end_time_=body.end_time,
        capacity=body.capacity,
        status=body.status,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found or not owned by provider")
    return row


@router.post("/{provider_id}/sessions/{session_id}/cancel")
def api_cancel_session(provider_id: int, session_id: int):
    """
    醫師取消門診（將 status 設為 0 = 停診）。
    """
    ok = cancel_clinic_session(provider_id, session_id, cancel_status=0)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found or not owned by provider")
    return {"success": True}



@router.get("/{provider_id}/sessions/{session_id}/appointments")
def api_list_appointments(provider_id: int, session_id: int):
    return list_appointments_for_session(provider_id, session_id)


@router.get("/{provider_id}/appointments/{appt_id}/encounter")
def api_get_encounter(provider_id: int, appt_id: int):
    row = get_encounter_by_appt(provider_id, appt_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return row


@router.put("/{provider_id}/appointments/{appt_id}/encounter")
def api_upsert_encounter(provider_id: int, appt_id: int, body: EncounterUpsert):
    return upsert_encounter(
        provider_user_id=provider_id,
        appt_id=appt_id,
        status=body.status,
        chief_complaint=body.chief_complaint,
        subjective=body.subjective,
        assessment=body.assessment,
        plan=body.plan,
    )


@router.get("/{provider_id}/encounters/{enct_id}/diagnoses")
def api_get_diagnoses(provider_id: int, enct_id: int):
    return list_diagnoses_for_encounter(enct_id)


@router.put("/{provider_id}/encounters/{enct_id}/diagnoses/{code_icd}")
def api_upsert_dx(provider_id: int, enct_id: int, code_icd: str, body: DiagnosisUpsert):
    upsert_diagnosis(enct_id, code_icd, body.is_primary)
    return list_diagnoses_for_encounter(enct_id)


@router.post("/{provider_id}/encounters/{enct_id}/primary-diagnosis")
def api_set_primary_dx(provider_id: int, enct_id: int, body: PrimaryDiagnosisBody):
    set_primary_diagnosis(enct_id, body.code_icd)
    return list_diagnoses_for_encounter(enct_id)


@router.get("/{provider_id}/encounters/{enct_id}/prescription")
def api_get_rx(provider_id: int, enct_id: int):
    rx = get_prescription_for_encounter(enct_id)
    if rx is None:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return rx


@router.put("/{provider_id}/encounters/{enct_id}/prescription")
def api_upsert_rx(provider_id: int, enct_id: int, body: PrescriptionUpsert):
    header = upsert_prescription_for_encounter(enct_id, body.status)
    rx_id = header["rx_id"]
    items_dicts = [item.dict() for item in body.items]
    replace_prescription_items(rx_id, items_dicts)
    return get_prescription_for_encounter(enct_id)
