from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Integer, ForeignKey, func, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
if TYPE_CHECKING:
  from app.models.service import Service


class Area(Base):
  __tablename__ = "areas"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
  x1: Mapped[int] = mapped_column(Integer, nullable=False)
  x2: Mapped[int] = mapped_column(Integer, nullable=False)
  y1: Mapped[int] = mapped_column(Integer, nullable=False)
  y2: Mapped[int] = mapped_column(Integer, nullable=False)
  origin_text: Mapped[str] = mapped_column(String, nullable=True)
  translated_text: Mapped[str] = mapped_column(String, nullable=True)
  service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

  service: Mapped["Service"] = relationship("Service", uselist=False)