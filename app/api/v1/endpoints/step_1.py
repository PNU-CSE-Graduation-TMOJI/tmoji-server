from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.responses.step_1 import start_service_response
from app.crud.image import read_image_by_filename
from app.crud.service import create_service
from app.db import get_db
from app.models.enums.service import Language, ServiceMode
from app.schemas.service import PostServiceRequest, ServiceCreate, ServiceRead
from app.utils.enum_to_html import enum_to_html

router = APIRouter()
  
@router.post(
  "/service", 
  summary="번역 서비스 시작", 
  description=
    f"""
      번역 서비스 선택 및 언어를 선택하여 서비스를 생성(시작)합니다. <br>
      {enum_to_html(Language)}
      {enum_to_html(ServiceMode)}
    """,
  response_model=ServiceRead,
  responses=start_service_response(),
  status_code=201
)
async def start_service(request: PostServiceRequest, db: AsyncSession = Depends(get_db)):
  # 1. 이미지 조회
  image = await read_image_by_filename(db, request.filename)
  if not image:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 이미지입니다.")
  
  # 2. 서비스 생성
  service_in = ServiceCreate(
    origin_image_id=image.id,
    origin_language=request.origin_language,
    mode=request.service_mode
  )
  service = await create_service(db, service_in)
  return service
  