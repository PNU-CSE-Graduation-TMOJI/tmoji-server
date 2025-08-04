from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1.routers import api_router

from app.load_env import load_environment

load_environment()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # FIXME torch 모델 로딩 여기에

    yield  # 여기서 FastAPI 앱이 실행됨

    # 앱 종료 시 (필요하면 여기 추가)
    print("🛑 Shutting down...")

app = FastAPI(
    title="Tmoji BackEnd Server",
    description="API for Tmoji Web",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Hello World"}