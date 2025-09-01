from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.image import read_image_by_id
from app.crud.service import read_service_by_id
from app.db import get_db
from app.schemas.service import ServiceDetail

router = APIRouter()

@router.get(
  "/{service_id}",
  summary="해당 Service 정보 조회",
  description=
    f"""
    ID와 일치하는 서비스의 OCR 정보를 반환합니다.
    """,
  status_code=status.HTTP_200_OK,
  response_model=ServiceDetail
)
async def get_service_by_id(service_id: str, db: AsyncSession = Depends(get_db)):
  service_id_num = int(service_id)

  # 1. 서비스 조회 & 유효성 검사
  service = await read_service_by_id(db, service_id_num)
  if not service:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 서비스입니다.")
  
  origin_image = await read_image_by_id(db, service.origin_image_id)
  if not origin_image:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="처리 중 에러가 발생하였습니다.")
  
  composed_image = await read_image_by_id(db, service.composed_image_id) if service.composed_image_id else None

  serviceDetail = ServiceDetail(
    id= service.id,
    origin_image_id=service.origin_image_id,
    composed_image_id=service.composed_image_id,
    mode=service.mode,
    step=service.step,
    status= service.status,
    origin_language=service.origin_language,
    target_language= service.target_language,
    created_at= service.created_at,
    origin_image=origin_image,
    composed_image=composed_image,
  )

  return serviceDetail
