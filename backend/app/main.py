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
