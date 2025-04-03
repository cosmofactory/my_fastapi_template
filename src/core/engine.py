from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

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


class Base(AsyncAttrs, DeclarativeBase):
    """
    Base class for ORM models.

    AsyncAttrs is needed to use attributes of the model that are part of another model.
    If you get MissingGreenlet exception while working with ORM models, add this:
        trip.locations - MissingGreenlet exception
        trip.awaitable_attrs.locations - works fine
    Wanna know more?
    https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#preventing-implicit-io-when-using-asyncsession
    """

    pass
