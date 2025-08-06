import os
from urllib.parse import quote_plus
from app.load_env import load_environment

load_environment()

def get_env_var(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return value

POSTGRES_USER = get_env_var("POSTGRES_USER")
POSTGRES_PASSWORD = quote_plus(get_env_var("POSTGRES_PASSWORD"))  # 특수문자 인코딩
POSTGRES_DB = get_env_var("POSTGRES_DB")
POSTGRES_HOST = get_env_var("POSTGRES_HOST")
POSTGRES_PORT = get_env_var("POSTGRES_PORT")

DATABASE_URL = (
    f'postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}'
    f'@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
)