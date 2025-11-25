# main.py
from fastapi import FastAPI

# 兩個子 router (專案拆分)
from .routers import patient_router, provider_router

app = FastAPI(title="Clinic Digital System API")

# 掛載 provider 專用路由
app.include_router(provider_router, prefix="/provider", tags=["provider"])

# 掛載 patient 專用路由
app.include_router(patient_router, prefix="/patient", tags=["patient"])


@app.get("/")
def root():
    return {"message": "Welcome to Clinic Digital System API"}
