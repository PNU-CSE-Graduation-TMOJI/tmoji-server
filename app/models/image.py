from datetime import datetime
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Image(Base):
  __tablename__ = "images"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
  filename: Mapped[str] = mapped_column(String, nullable=False)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())