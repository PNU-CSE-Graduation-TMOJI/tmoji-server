from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.tx import tx
from app.models.image import Image
from app.schemas.image import ImageCreate, ImageRead


async def create_image(db: AsyncSession, image_in: ImageCreate) -> ImageRead:
  async with tx(db):
    db_image = Image(
      filename = image_in.filename,
    )
    db.add(db_image)
    await db.flush()
    await db.refresh(db_image)

  return ImageRead.model_validate(db_image)

async def read_image_by_id(db: AsyncSession, id: int) -> ImageRead | None:
  async with tx(db, nested=False):
    result = await db.execute(select(Image).where(Image.id == id))
    image = result.scalars().first()
  return ImageRead.model_validate(image) if image else None

async def read_image_by_filename(db: AsyncSession, filename: str) -> ImageRead | None:
  async with tx(db, nested=False):
    result = await db.execute(select(Image).where(Image.filename == filename))
    image = result.scalars().first()
  return ImageRead.model_validate(image) if image else None