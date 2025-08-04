from datetime import datetime
from app.schemas.base import CommonModel

class AreaBase(CommonModel):
  x1: int
  x2: int
  y1: int
  y2: int
  service_id: int

class AreaCreate(AreaBase):
  pass

class AreaRead(AreaBase):
  id: int
  created_at: datetime

  class Config:
    orm_mode = True

class AreaUpdate(CommonModel):
  origin_text: str | None = None
  translated_text: str | None = None
