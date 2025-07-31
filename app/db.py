import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from urllib.parse import quote_plus
import psycopg
from dotenv import load_dotenv

load_dotenv()

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

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_connection() -> psycopg.Connection:
    try:
        conn = psycopg.connect(DATABASE_URL, connect_timeout=5)
        return conn
    except psycopg.OperationalError as e:
        print(f"Database connection failed: {e}")
        raise

def test_db_connection():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ DB 연결 성공:", result.scalar())
    except Exception as e:
        print("❌ DB 연결 실패:", e)