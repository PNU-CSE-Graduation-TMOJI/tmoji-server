from sqlalchemy.ext.asyncio import AsyncSession
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceRead

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
