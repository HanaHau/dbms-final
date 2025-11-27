# main.py
from fastapi import FastAPI
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
