from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.engine import async_session_maker


async def get_async_session() -> AsyncGenerator[AsyncSession, None, None]:
    """Get local database connection."""
    async with async_session_maker() as session:
        yield session


# Dependency to use with ORM models
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
