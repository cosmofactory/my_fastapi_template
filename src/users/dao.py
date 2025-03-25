import logfire
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.base_dao import BaseDAO
from src.users.models import User


class UserDAO(BaseDAO):
    model = User

    @classmethod
    @logfire.instrument()
    async def get_user_by_email(cls, session: AsyncSession, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        result = await session.execute(statement)
        if obj := result.first():
            return obj[0]
        return None
