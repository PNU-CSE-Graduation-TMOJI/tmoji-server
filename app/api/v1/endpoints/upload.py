from io import BytesIO
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from app.api.v1.responses.image import upload_image_response
from app.crud.image import create_image
from app.db import get_db
from app.schemas.image import ImageCreate, ImageRead

router = APIRouter()

@router.post(
  "", 
  summary="이미지 업로드", 
  description="이미지를 업로드하고 저장된 파일의 이름을 반환합니다.",
  response_model=ImageRead,
  responses=upload_image_response()
)
async def upload_image(file: UploadFile, db: Session = Depends(get_db)):
  UPLOAD_DIR = './photo/origin'
  os.makedirs(UPLOAD_DIR, exist_ok=True)

  try:
    content = await file.read()
    image = Image.open(BytesIO(content))

    # PNG로 변환
    image = image.convert("RGBA")
    filename = f"{str(uuid.uuid4())}.png"
    save_path = os.path.join(UPLOAD_DIR, filename)
    image.save(save_path, format="PNG")
    image_in = ImageCreate(filename=filename)

    return create_image(db, image_in=image_in)

  except Exception as e:
    raise HTTPException(status_code=400, detail=f"이미지 처리 실패: {str(e)}")