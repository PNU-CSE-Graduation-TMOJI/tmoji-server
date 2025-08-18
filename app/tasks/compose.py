# pyright: reportUnknownMemberType=false, reportAttributeAccessIssue=false, reportUnknownVariableType=false

import asyncio
from app.celery_app import celery
from typing import TypedDict
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.constants.database_url import DATABASE_URL
from app.crud.area import read_areas_bulk_by_service_id
from app.crud.image import create_image, read_image_by_id
from app.crud.service import read_service_by_id, update_service
from app.models.enums.service import ServiceMode, ServiceStatus, ServiceStep
from app.schemas.image import ImageCreate
from app.schemas.service import ServiceRead, ServiceUpdate

from PIL import ImageDraw, ImageFont

from app.utils.storage import build_storage


# --- 워커 전용 세션팩토리 ---
_engine = create_async_engine(DATABASE_URL, future=True)
SessionLocal = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)

storage = build_storage()

def get_resized_font(
  text: str,
  max_width: int,
  max_height: int,
  font_path: str,
  min_font_size: int = 5,
  max_font_size: int = 100
) -> ImageFont.FreeTypeFont:
  """
  텍스트가 max_width와 max_height 안에 최대한 꽉 차도록 폰트 크기를 조절.
  """
  best_font = ImageFont.truetype(font_path, min_font_size)
  for font_size in range(min_font_size, max_font_size + 1):
      font = ImageFont.truetype(font_path, font_size)
      bbox = font.getbbox(text)
      text_width = bbox[2] - bbox[0]
      text_height = bbox[3] - bbox[1]

      if text_width > max_width or text_height > max_height:
          # 넘었으면 이전 크기로 반환
          return best_font
      best_font = font

  return best_font

async def compose_image_machine_mode(db: AsyncSession, service: ServiceRead) -> None:
  origin_image_read = await read_image_by_id(db, service.origin_image_id)

  if not origin_image_read:
    raise Exception("id와 일치하는 image를 찾을 수 없습니다.")
  
  imageFile = storage.load_image(origin_image_read.filename, "upload")
  draw = ImageDraw.Draw(imageFile)
  
  areas = await read_areas_bulk_by_service_id(db, service.id)\
  
  for area in areas:
    draw.rectangle([(area.x1, area.y1), (area.x2, area.y2)], fill="white")
    text = area.translated_text or "error"

    box_width = area.x2 - area.x1
    box_height = area.y2 - area.y1
    font = get_resized_font(text, box_width - 10, box_height - 10, './font/PretendardJP-Regular.ttf')

    text_position = (area.x1 + 5, area.y1 + 5)
    draw.text(text_position, text, fill="black", font=font)
  
  composed_filename = f"composed_{origin_image_read.filename}"
  storage.save_png(imageFile, composed_filename, target="compose")

  created_image = await create_image(db, image_in=ImageCreate(filename=composed_filename))
  service_in = ServiceUpdate(composed_image_id=created_image.id)
  await update_service(db, service.id, service_in=service_in)



async def compose_image_ai_mode(db: AsyncSession, service: ServiceRead) -> None:
  # FIXME 학습된 AI 모델과 연결해야함!!
  await compose_image_machine_mode(db, service)

class ComposePayload(TypedDict):
  service_id: int

@celery.task
def compose_image(payload: ComposePayload) -> bool:
    """Celery 워커에서 실행되는 동기 엔트리. 내부에서 async 실행."""
    async def _run() -> bool:
      async with SessionLocal() as db:
        service = await read_service_by_id(db, payload["service_id"])
        if not service:
          raise Exception("id와 일치하는 service를 찾을 수 없습니다.")
        
        if service.mode == ServiceMode.AI:
          await compose_image_ai_mode(db, service)
        else:
          await compose_image_machine_mode(db, service)
          
        service_in = ServiceUpdate(step=ServiceStep.COMPOSING, status=ServiceStatus.COMPLETED)
        await update_service(db, service.id, service_in)

      return True

    return asyncio.run(_run())