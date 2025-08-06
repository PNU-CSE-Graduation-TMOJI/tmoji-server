from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

@asynccontextmanager
async def tx(db: AsyncSession, *, nested: bool = True):
    """
    트랜잭션 컨텍스트 매니저.
    - 현재 트랜잭션이 있으면 SAVEPOINT(begin_nested)로 중첩
    - 없으면 새 트랜잭션(begin)
    - 성공 시 COMMIT, 예외 시 ROLLBACK 자동
    """
    if nested and db.in_transaction():
        async with db.begin_nested():
            try:
                yield db
            except Exception:
                logger.exception("Transaction (nested) rolled back due to error")
                raise
    else:
        async with db.begin():
            try:
                yield db
            except Exception:
                logger.exception("Transaction rolled back due to error")
                raise