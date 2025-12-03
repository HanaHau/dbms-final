# main.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

# 兩個子 router (專案拆分)
from .routers import patient_router, provider_router

app = FastAPI(title="Clinic Digital System API")

# 設定 CORS
# 開發環境：允許所有來源；生產環境：只允許特定來源
allowed_origins = [
    "http://localhost:5173",  # Vite 預設端口
    "http://localhost:3000",  # React 預設端口
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

# 如果是開發環境，允許所有來源
if os.getenv("ENVIRONMENT", "development") == "development":
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 掛載 provider 專用路由
app.include_router(provider_router, prefix="/provider", tags=["provider"])

# 掛載 patient 專用路由
app.include_router(patient_router, prefix="/patient", tags=["patient"])


@app.on_event("startup")
async def startup_event():
    """應用程式啟動時執行初始化任務"""
    try:
        # 處理門診結束後未報到的病人，累計爽約次數
        from .repositories import AppointmentRepository, PatientRepository, SessionRepository
        from psycopg2.extras import RealDictCursor
        from .pg_base import get_pg_conn
        from datetime import datetime
        
        print("正在處理門診結束後未報到的掛號...")
        conn = get_pg_conn()
        try:
            conn.autocommit = False
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 找出所有已結束的門診時段中，狀態為「已預約」(1) 或「未報到」(5) 的掛號
                cur.execute(
                    """
                    SELECT DISTINCT a.patient_id, a.appt_id, a.session_id
                    FROM APPOINTMENT a
                    JOIN CLINIC_SESSION cs ON a.session_id = cs.session_id
                    LEFT JOIN LATERAL (
                        SELECT ash.to_status
                        FROM APPOINTMENT_STATUS_HISTORY ash
                        WHERE ash.appt_id = a.appt_id
                        ORDER BY ash.changed_at DESC
                        LIMIT 1
                    ) AS ash_latest ON TRUE
                    WHERE COALESCE(ash_latest.to_status, 1) IN (1, 5)  -- 已預約或未報到
                      AND (cs.date < CURRENT_DATE 
                           OR (cs.date = CURRENT_DATE AND cs.end_time < CURRENT_TIME))
                      AND NOT EXISTS (
                          -- 排除已經處理過的（已經有就診記錄的）
                          SELECT 1 FROM ENCOUNTER e WHERE e.appt_id = a.appt_id
                      );
                    """,
                )
                
                no_show_appointments = cur.fetchall()
                
                processed_count = 0
                for row in no_show_appointments:
                    patient_id = row["patient_id"]
                    appt_id = row["appt_id"]
                    session_id = row["session_id"]
                    
                    # 獲取 provider_id
                    cur.execute(
                        """
                        SELECT provider_id FROM CLINIC_SESSION
                        WHERE session_id = %s;
                        """,
                        (session_id,)
                    )
                    session_row = cur.fetchone()
                    if not session_row:
                        continue
                    
                    provider_id = session_row["provider_id"]
                    
                    # 檢查是否已經標記為未報到
                    current_status = AppointmentRepository._get_latest_status(conn, appt_id)
                    if current_status != 5:  # 如果還不是未報到狀態
                        # 將掛號狀態更新為「未報到」(5)
                        AppointmentRepository._insert_status_history(
                            conn, appt_id, current_status, 5, provider_id
                        )
                        
                        # 累計爽約次數
                        PatientRepository.increment_no_show_count(patient_id)
                    
                    processed_count += 1
                
                conn.commit()
                if processed_count > 0:
                    print(f"✅ 已處理 {processed_count} 個未報到的掛號")
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"⚠️ 啟動時處理未報到掛號失敗: {e}")
        finally:
            if conn:
                conn.close()
    except Exception as e:
        print(f"⚠️ 啟動事件執行失敗: {e}")


@app.get("/")
def root():
    return {"message": "Welcome to Clinic Digital System API"}


@app.get("/departments")
def api_list_departments():
    """
    列出所有部門。
    回傳格式：
    [
      { "dept_id": 1, "name": "內科", "location": "..." },
      ...
    ]
    """
    from .repositories import DepartmentRepository
    repo = DepartmentRepository()
    return repo.list_all_departments()


@app.get("/departments/by-name")
def api_get_department_by_name(name: str = Query(...)):
    """
    根據部門名稱取得部門資訊。
    回傳格式：
    { "dept_id": 1, "name": "內科", "location": "..." }
    如果找不到則回傳 404。
    """
    from .repositories import DepartmentRepository
    
    repo = DepartmentRepository()
    department = repo.get_department_by_name(name)
    
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    
    return department
