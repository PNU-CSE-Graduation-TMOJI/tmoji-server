from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.image import Image
from app.schemas.image import ImageCreate, ImageRead


async def create_image(db: AsyncSession, image_in: ImageCreate) -> ImageRead:
  try:
    print('add')
    db_image = Image(
      filename = image_in.filename,
    )
    db.add(db_image)

    print('flush')
    await db.flush()
    print('refresh')
    await db.refresh(db_image)
    print('commit')
    await db.commit()

    print('return')
    return ImageRead.model_validate(db_image)
  except Exception:
    await db.rollback()
    raise

async def read_image_by_id(db: AsyncSession, id: int) -> ImageRead | None:
  result = await db.execute(select(Image).where(Image.id == id))
  image = result.scalars().first()
  return ImageRead.model_validate(image) if image else None

async def read_image_by_filename(db: AsyncSession, filename: str) -> ImageRead | None:
  result = await db.execute(select(Image).where(Image.filename == filename))
  image = result.scalars().first()
  return ImageRead.model_validate(image) if image else None