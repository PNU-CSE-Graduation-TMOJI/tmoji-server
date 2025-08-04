from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import DateTime, Integer, ForeignKey, func, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.enums.service import Language, ServiceMode, ServiceStatus, ServiceStep
if TYPE_CHECKING:
  from app.models.image import Image
  from app.models.area import Area


class Service(Base):
  __tablename__ = "services"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
  origin_image_id: Mapped[int] = mapped_column(ForeignKey("images.id"), nullable=False)
  mode : Mapped[ServiceMode] = mapped_column(SqlEnum(ServiceMode), name="service_mode", nullable=False)
  step: Mapped[ServiceStep] = mapped_column(SqlEnum(ServiceStep), name="service_step", nullable=False, server_default=ServiceStep.BOUNDING)
  status: Mapped[ServiceStatus] = mapped_column(SqlEnum(ServiceStatus), name="service_status", nullable=False, server_default=ServiceStatus.PENDING)
  origin_language: Mapped[Language] = mapped_column(SqlEnum(Language), name="origin_language", nullable=False)
  target_language: Mapped[Language] = mapped_column(SqlEnum(Language), name="target_language", nullable=True)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

  image: Mapped["Image"] = relationship("Image", uselist=False)
  areas: Mapped[List["Area"]] = relationship("Area", back_populates="service")