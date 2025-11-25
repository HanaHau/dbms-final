# routers/__init__.py
from .patient_router import router as patient_router
from .provider_router import router as provider_router

__all__ = ["patient_router", "provider_router"]

