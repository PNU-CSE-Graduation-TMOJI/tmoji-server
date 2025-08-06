from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tx import tx
from app.models.area import Area
from app.schemas.area import AreaCreate, AreaRead, AreaUpdate

async def create_areas_bulk(db: AsyncSession, areas_in: List[AreaCreate]) -> List[AreaRead]:
  async with tx(db):
    db_areas = [Area(
      x1 = area.x1,
      x2 = area.x2,
      y1 = area.y1,
      y2 = area.y2,
      service_id = area.service_id,
      area_image_id = area.area_image_id,
    ) for area in areas_in]
    db.add_all(db_areas)

  for area in db_areas:
    await db.refresh(area)

  return [AreaRead.model_validate(area) for area in db_areas]

async def update_area(db: AsyncSession, area_in: AreaUpdate) -> AreaRead:
  async with tx(db):
      area = await db.get(Area, area_in.id)
      if not area:
        raise Exception('Area no exist')
      
      if area_in.origin_text is not None:
        area.origin_text = area_in.origin_text
      if area_in.translated_text is not None:
        area.translated_text = area_in.translated_text
  
  return AreaRead.model_validate(area)

async def read_areas_bulk_by_service_id(db: AsyncSession, service_id: int) -> List[AreaRead]:
  async with tx(db, nested=False):
    result = await db.execute(select(Area).where(Area.service_id == service_id))
    areas = result.scalars().all()
  return [AreaRead.model_validate(area) for area in areas]

async def read_area_by_id(db: AsyncSession, area_id: int) -> AreaRead | None:
  async with tx(db):
    result = await db.execute(select(Area).where(Area.id == area_id))
    area = result.scalars().first()
  return AreaRead.model_validate(area) if area else None

async def delete_area_by_id(db: AsyncSession, area_id: int) -> None:
  async with tx(db):
    area = await db.get(Area, area_id)
    if area:
      await db.delete(area)
    else:
      raise Exception('Area no exist')