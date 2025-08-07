# pyright: reportUnknownMemberType=false, reportAttributeAccessIssue=false, reportUnknownVariableType=false

import asyncio
from app.celery_app import celery
from typing import TypedDict
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.constants.database_url import DATABASE_URL
from app.crud.area import read_areas_bulk_by_service_id, update_area
from app.crud.service import update_service
from app.models.enums.service import Language, ServiceStatus, ServiceStep
from app.schemas.area import AreaUpdate
from app.schemas.service import ServiceUpdate
from app.utils.google_translate import translate_text


# --- 워커 전용 세션팩토리 ---
_engine = create_async_engine(DATABASE_URL, future=True)
SessionLocal = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)


class TranslatePayload(TypedDict):
  service_id: int
  origin_language: Language
  target_language: Language

@celery.task
def translate_areas(payload: TranslatePayload, service_id: int) -> bool:
    """Celery 워커에서 실행되는 동기 엔트리. 내부에서 async 실행."""
    async def _run() -> bool:
      async with SessionLocal() as db:
        areas = await read_areas_bulk_by_service_id(db, service_id)
        
        for area in areas:
          translated_text = translate_text(payload["target_language"], payload["origin_language"], area.origin_text or '')
          area_in = AreaUpdate(id=area.id, translated_text=translated_text)
          await update_area(db, area_in)
          
        service_in = ServiceUpdate(step=ServiceStep.TRANSLATING, status=ServiceStatus.PENDING)
        await update_service(db, service_id, service_in)

      return True

    return asyncio.run(_run())