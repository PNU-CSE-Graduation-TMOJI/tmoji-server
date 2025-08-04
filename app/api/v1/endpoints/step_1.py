from io import BytesIO
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from PIL import Image as PILImage
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.responses.step_1 import start_service_response, upload_image_response
from app.crud.image import create_image, read_image_by_filename
from app.crud.service import create_service
from app.db import get_db
from app.models.enums.service import Language, ServiceMode
from app.schemas.image import ImageCreate, ImageRead
from app.schemas.service import PostServiceRequest, ServiceCreate, ServiceRead
from app.utils.enum_to_html import enum_to_html

router = APIRouter()

@router.post(
  "/image", 
  summary="이미지 업로드", 
  description="이미지를 업로드하고 저장된 파일의 이름을 반환합니다.",
  response_model=ImageRead,
  responses=upload_image_response(),
  status_code=201
)
async def upload_image(file: UploadFile, db: AsyncSession = Depends(get_db)):
  UPLOAD_DIR = './photo/origin'
  os.makedirs(UPLOAD_DIR, exist_ok=True)

  try:
    # PNG로 변환
    content = await file.read()
    pil_img = PILImage.open(BytesIO(content)).convert("RGBA")

    filename = f"{str(uuid.uuid4())}.png"
    save_path = os.path.join(UPLOAD_DIR, filename)
    pil_img.save(save_path, format="PNG")

    image_in = ImageCreate(filename=filename)
    return await create_image(db, image_in=image_in)

  except Exception as e:
    print(str(e))
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"이미지 처리 실패")
  
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
  