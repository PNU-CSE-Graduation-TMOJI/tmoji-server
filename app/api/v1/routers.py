from fastapi import APIRouter
from app.api.v1.endpoints import step_1

api_router = APIRouter()
api_router.include_router(step_1.router, prefix="/step-1", tags=["STEP-1"])