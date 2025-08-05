from datetime import datetime
from typing import List
from app.schemas.base import CommonModel

class AreaBase(CommonModel):
  x1: int
  x2: int
  y1: int
  y2: int

class AreaCreate(AreaBase):
  service_id: int
  area_image_id: int

class AreaRead(AreaBase):
  id: int
  created_at: datetime
  service_id: int

  class Config:
    orm_mode = True

class AreaUpdate(CommonModel):
  origin_text: str | None = None
  translated_text: str | None = None


# API Request Body & Parameters
class PostAreaRequest(CommonModel):
  service_id: int
  areas: List[AreaBase]