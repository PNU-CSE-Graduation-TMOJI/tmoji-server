from fastapi import APIRouter
from app.api.v1.endpoints import upload

api_router = APIRouter()
api_router.include_router(upload.router, prefix="/upload", tags=["STEP-1"])