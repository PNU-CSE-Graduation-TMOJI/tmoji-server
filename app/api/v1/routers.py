from fastapi import APIRouter
from app.api.v1.endpoints import image, step_1, step_2, step_3, step_4

api_router = APIRouter()
api_router.include_router(image.router, prefix="/image", tags=["image"])
api_router.include_router(step_1.router, prefix="/step-1", tags=["STEP-1"])
api_router.include_router(step_2.router, prefix="/step-2", tags=["STEP-2"])
api_router.include_router(step_3.router, prefix="/step-3", tags=["STEP-3"])
api_router.include_router(step_4.router, prefix="/step-4", tags=["STEP-4"])