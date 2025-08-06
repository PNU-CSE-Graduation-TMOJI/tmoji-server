import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image as PILImage

from app.constants.image_path import CROP_DIR, UPLOAD_DIR
from app.crud.area import create_areas_bulk
from app.crud.image import create_image, read_image_by_id
from app.crud.service import read_service_by_id, update_service
from app.db import get_db
from app.models.enums.service import Language, ServiceMode, ServiceStep, ServiceStatus
from app.schemas.area import AreaCreate, PostAreaRequest
from app.schemas.image import ImageCreate, ImageRead
from app.schemas.service import ServiceUpdate
from app.utils.enum_to_html import enum_to_html
from app.tasks.ocr import AreaPayload, extract_areas

router = APIRouter()

@router.post(
  "/areas", 
  summary="텍스트 영역 지정", 
  description=
    f"""
      번역 서비스 선택 및 언어를 선택하여 서비스를 생성(시작)합니다. <br>
      {enum_to_html(Language)}
      {enum_to_html(ServiceMode)}
    """,
  status_code=status.HTTP_202_ACCEPTED
)
async def make_area(request: PostAreaRequest, db: AsyncSession = Depends(get_db)):
  # 0. 유효성 검사
  if len(request.areas) == 0 :
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="area가 비어 있습니다.")
  
  # 1. 서비스 조회
  service = await read_service_by_id(db, request.service_id)
  if not service:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 서비스입니다.")
  if service.step != ServiceStep.BOUNDING:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{service.step} 단계의 서비스는 영역을 생성할 수 없습니다.")
  
  # 2. 잘라낸 이미지 저장
  originImage = await read_image_by_id(db, service.origin_image_id)
  if not originImage:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="서버 오류가 발생하였습니다.")
  
  cropped_images: List[ImageRead] = []
  originImageFile = PILImage.open(os.path.join(UPLOAD_DIR, originImage.filename))

  os.makedirs(CROP_DIR, exist_ok=True)
  for i, area in enumerate(request.areas):
    cropped = originImageFile.crop((area.x1, area.y1, area.x2, area.y2))

    cropped_filename = f'{originImage.filename[:-4]}_{i+1}.png'
    cropped_save_path = os.path.join(CROP_DIR, cropped_filename)
    cropped.save(cropped_save_path, format="PNG")

    image_db = await create_image(db, image_in=ImageCreate(filename=cropped_filename))
    cropped_images.append(image_db)

  # 3. 영역(바운딩 박스) DB 기록
  areas_in = [AreaCreate(
    x1=area.x1,
    x2=area.x2,
    y1=area.y1,
    y2=area.y2,
    service_id=request.service_id,
    area_image_id=cropped_images[i].id,
  ) for i, area in enumerate(request.areas)]

  areas = await create_areas_bulk(db, areas_in)

  # 4. 서비스 step 전환
  service_in = ServiceUpdate(
    step=ServiceStep.DETECTING,
    status=ServiceStatus.PROCESSING,
  )
  service = await update_service(db=db, id=service.id, service_in=service_in)

  # 5. OCR 진행
  payloads: List[AreaPayload] = []
  for i, area in enumerate(areas):
    area_pay_load = AreaPayload(
      area_id=area.id,
      image_path=os.path.join(CROP_DIR, cropped_images[i].filename),
      lang=service.origin_language.value,
    )
    payloads.append(area_pay_load)

  extract_areas.delay(payloads, service.id) # pyright: ignore[reportFunctionMemberAccess]

  return service
  