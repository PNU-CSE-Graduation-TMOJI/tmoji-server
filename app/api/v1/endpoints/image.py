from io import BytesIO
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image as PILImage
from app.api.v1.responses.image import upload_image_response
from app.crud.image import create_image
from app.db import get_db
from app.schemas.image import ImageCreate, ImageRead

from app.utils.storage import Target, build_storage


router = APIRouter()
storage = build_storage()

def pick_target(filename: str) -> Target:
  return "compose" if "composed_" in filename else "upload"

@router.get(
  "/{filename}",
  summary="png 이미지 제공",
  status_code=status.HTTP_200_OK,
)
async def get_image(filename: str):
  target = pick_target(filename)

  return storage.get_image_response(filename, target)

@router.post(
  "", 
  summary="이미지 업로드", 
  description="이미지를 업로드하고 저장된 파일의 이름을 반환합니다.",
  response_model=ImageRead,
  responses=upload_image_response(),
  status_code=201
)
async def upload_image(file: UploadFile, db: AsyncSession = Depends(get_db)):
  try:
    # PNG로 변환
    content = await file.read()
    pil_img = PILImage.open(BytesIO(content)).convert("RGBA")

    filename = f"{str(uuid.uuid4())}.png"

    storage.save_png(pil_img, filename, target="upload")

    image_in = ImageCreate(filename=filename)
    return await create_image(db, image_in=image_in)

  except HTTPException:
    raise
  except Exception as e:
      print(f"[upload_image] error: {e}")
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="이미지 처리 실패")
