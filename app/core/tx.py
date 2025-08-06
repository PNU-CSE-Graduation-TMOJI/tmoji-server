from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

@asynccontextmanager
async def tx(db: AsyncSession, *, nested: bool = True):
    commit = False
    if nested and db.in_transaction():
        async with db.begin_nested():
            try:
                yield db
                commit = True
            except Exception:
                logger.exception("Transaction (nested) rolled back due to error")
                raise
    else:
        async with db.begin():
            try:
                yield db
                commit = True
            except Exception:
                logger.exception("Transaction rolled back due to error")
                raise
    if commit:
        await db.commit()