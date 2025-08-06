from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.constants.database_url import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=True)

SessionLocal = async_sessionmaker(
    expire_on_commit=False, 
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    class_=AsyncSession,
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with SessionLocal() as session:
        yield session
