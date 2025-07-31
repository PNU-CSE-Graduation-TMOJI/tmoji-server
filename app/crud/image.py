from sqlalchemy.orm import Session
from app.models.image import Image
from app.schemas.image import ImageCreate


def create_image(db: Session, image_in: ImageCreate) -> Image:
  db_image = Image(
    filename = image_in.filename,
  )
  db.add(db_image)
  db.commit()
  db.refresh(db_image)
  return db_image