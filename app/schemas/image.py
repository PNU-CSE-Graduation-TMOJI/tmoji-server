from datetime import datetime
from app.schemas.base import CommonModel

class ImageBase(CommonModel):
  filename: str

class ImageCreate(ImageBase):
  pass

class ImageRead(ImageBase):
  id: int
  created_at: datetime
