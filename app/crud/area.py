from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.area import Area
from app.schemas.area import AreaCreate, AreaRead

async def create_areas_bulk(db: AsyncSession, areas_in: List[AreaCreate]) -> List[AreaRead]:
  db_areas = [Area(
    x1 = area.x1,
    x2 = area.x2,
    y1 = area.y1,
    y2 = area.y2,
    service_id = area.service_id,
    area_image_id = area.area_image_id,
  ) for area in areas_in]
  db.add_all(db_areas)
  await db.commit()

  for area in db_areas:
    await db.refresh(area)

  return [AreaRead.model_validate(area) for area in db_areas]