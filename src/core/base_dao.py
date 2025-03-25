from dataclasses import dataclass
from typing import Type, TypeVar

import logfire
from fastapi import HTTPException, status
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import BinaryExpression
from sqlmodel import SQLModel, col, select

T = TypeVar("T", bound=SQLModel)


@dataclass
class FilterCondition:
    """
    Wraps a SQLAlchemy BinaryExpression by converting its left-hand side into a qualified column.

    """

    def __init__(self, expression: BinaryExpression):
        if not isinstance(expression, BinaryExpression):
            raise ValueError("Single argument must be a SQLAlchemy expression")
        self.expression = expression

    def to_expression(self):
        return BinaryExpression(
            col(self.expression.left),
            right=self.expression.right,
            operator=self.expression.operator,
        )


class BaseDAO:
    model: Type[T]

    @classmethod
    @logfire.instrument()
    async def get_all(
        cls,
        session: AsyncSession,
        limit: int | None = None,
        offset: int | None = None,
        filters: list[FilterCondition] | None = None,
    ) -> list[T]:
        statement = select(cls.model).offset(offset).limit(limit)
        if filters:
            for f in filters:
                statement = statement.where(f.to_expression())
        results: Result = await session.execute(statement)
        return results.scalars().all()

    @classmethod
    @logfire.instrument()
    async def get_first(
        cls,
        session: AsyncSession,
        filters: list[FilterCondition] | None = None,
    ) -> T | None:
        statement = select(cls.model)
        if filters:
            for f in filters:
                statement = statement.where(f.to_expression())
        results: Result = await session.execute(statement)
        return results.scalars().first()

    @classmethod
    @logfire.instrument()
    async def get_one_or_none(
        cls,
        session: AsyncSession,
        id: int,
    ) -> T | None:
        return await session.get(cls.model, id)

    @classmethod
    @logfire.instrument()
    async def get_object_or_404(
        cls,
        session: AsyncSession,
        id: int,
    ) -> T | HTTPException:
        if result := await session.get(cls.model, id):
            return result
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    @classmethod
    @logfire.instrument()
    async def create(
        cls,
        session: AsyncSession,
        email: str,
        password: str,  # TODO MAKE THIS TEMP
    ):
        obj = cls.model(email=email, password=password)
        session.add(obj)
        await session.commit()
