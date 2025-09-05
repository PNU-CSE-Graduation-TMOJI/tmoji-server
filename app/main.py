from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routers import api_router

from app.constants.client_url import CLIENT_URL
from app.load_env import load_environment

load_environment()

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield  # 여기서 FastAPI 앱이 실행됨

    # 앱 종료 시 (필요하면 여기 추가)
    print("🛑 Shutting down...")

app = FastAPI(
    title="Tmoji BackEnd Server",
    description="API for Tmoji Web",
    version="0.1.0",
    lifespan=lifespan
)

origins = [
    CLIENT_URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}