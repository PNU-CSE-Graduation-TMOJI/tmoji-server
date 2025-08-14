from datetime import datetime
from typing import List

from app.models.enums.service import Language, ServiceMode, ServiceStatus, ServiceStep
from app.schemas.area import AreaReadAfterDetecting, AreaReadAfterTranslating
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
  composed_image_id: int | None = None
  mode: ServiceMode
  step: ServiceStep
  status: ServiceStatus
  origin_language: Language
  target_language: Language | None = None
  created_at: datetime

class ServiceUpdate(ServiceBase):
  step: ServiceStep | None = None
  status: ServiceStatus | None = None
  target_language: Language | None = None
  composed_image_id: int | None = None


# Request Body
class PostServiceRequest(ServiceBase):
  filename: str
  origin_language: Language
  service_mode: ServiceMode

class PostServiceTranslateRequest(CommonModel):
  target_language: Language

# Response Body
class GetServiceDetectingStatusResponse(ServiceBase):
  isCompleted: bool
  id: int
  status: ServiceStatus
  areas: List[AreaReadAfterDetecting] | None

class GetServiceTranslatingStatusResponse(ServiceBase):
  isCompleted: bool
  id: int
  status: ServiceStatus
  areas: List[AreaReadAfterTranslating] | None

class GetServiceComposingStatusResponse(ServiceBase):
  isCompleted: bool
  id: int
  status: ServiceStatus
  composed_image_filename: str | None