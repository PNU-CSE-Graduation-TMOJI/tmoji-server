from datetime import datetime

from pydantic import Field
from app.models.enums.service import Language, ServiceMode, ServiceStatus, ServiceStep
from app.schemas.base import CommonModel

class ServiceBase(CommonModel):
  pass

class ServiceCreate(ServiceBase):
  origin_image_id: int
  origin_language: Language
  mode: ServiceMode

class ServiceRead(ServiceBase):
  id: int
  origin_image_id: int
  mode: ServiceMode
  step: ServiceStep
  status: ServiceStatus
  origin_language: Language
  target_language: Language | None = None
  created_at: datetime

class ServiceUpdate(ServiceBase):
  step: ServiceStep
  status: ServiceStatus
  target_language: Language | None = None


# Request Body
class PostServiceRequest(ServiceBase):
  filename: str = Field(description="이미지 파일 이름", examples=["d4104220-044d-4c52-a6ab-cf63b3223ef7.png"])
  origin_language: Language = Field(description="원본 이미지 언어", examples=list(Language))
  service_mode: ServiceMode = Field(description="서비스의 번역 모드", examples=list(ServiceMode))