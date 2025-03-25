from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.settings import settings

async_engine = create_async_engine(
    settings.database.DATABASE_URL,
    echo=True,
    future=True,
)


async_session_maker = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
