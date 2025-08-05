from typing import Any
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceRead, ServiceUpdate

async def create_service(db: AsyncSession, service_in: ServiceCreate) -> ServiceRead:
  db_service = Service(
    origin_image_id = service_in.origin_image_id,
    origin_language = service_in.origin_language,
    mode = service_in.mode
  )
  db.add(db_service)
  await db.commit()
  await db.refresh(db_service)
  return ServiceRead.model_validate(db_service)

async def read_service_by_id(db: AsyncSession, id: int) -> ServiceRead | None:
  result = await db.execute(select(Service).where(Service.id == id))
  service = result.scalars().first()
  return ServiceRead.model_validate(service) if service else None

async def update_service(db: AsyncSession, id: int, service_in: ServiceUpdate) -> ServiceRead:
  # 1) 대상 조회
  result = await db.execute(select(Service).where(Service.id == id))
  db_service = result.scalar_one_or_none()
  if not db_service:
    raise Exception('Service no exist')
  
  # 2) 부분 업데이트 (요청에 들어온 값만)
  payload: dict[str, Any] = service_in.model_dump(exclude_unset=True)
  
  for field, value in payload.items():
    setattr(db_service, field, value)

  # 3) 커밋/리프레시
  try:
      await db.commit()
      await db.refresh(db_service)
  except DBAPIError:
      await db.rollback()
      raise

  # 4) 스키마로 변환 후 반환
  return ServiceRead.model_validate(db_service)