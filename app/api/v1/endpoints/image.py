from io import BytesIO
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image as PILImage
from app.api.v1.responses.image import upload_image_response
from app.crud.image import create_image
from app.db import get_db
from app.schemas.image import ImageCreate, ImageRead

from app.constants.image_path import COMPOSE_DIR, UPLOAD_DIR


router = APIRouter()

@router.get(
  "/{filename}",
  summary="png 이미지 제공",
  status_code=status.HTTP_200_OK,
)
async def get_image(filename: str):
  prefix_path = UPLOAD_DIR
  if filename.find('composed_') > -1:
    prefix_path = COMPOSE_DIR

  dir_only = Path(prefix_path).resolve()
  name_only = Path(filename).name

  file_path = (dir_only / name_only).resolve()

  if not str(file_path).startswith(str(dir_only)):
    raise HTTPException(status_code=400, detail="경로가 잘못되었습니다.")
  
  if not file_path.exists():
    raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
  
  headers = {
    "Content-Disposition": f'inline; filename="{name_only}"',
    # 필요 시 캐시 정책 조절
    # "Cache-Control": "public, max-age=3600"
  }

  return FileResponse(
    path=file_path,
    media_type="image/png",
    headers=headers,
  )

@router.post(
  "", 
  summary="이미지 업로드", 
  description="이미지를 업로드하고 저장된 파일의 이름을 반환합니다.",
  response_model=ImageRead,
  responses=upload_image_response(),
  status_code=201
)
async def upload_image(file: UploadFile, db: AsyncSession = Depends(get_db)):
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
