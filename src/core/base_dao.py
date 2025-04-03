"""
Generic DAO Layer for SQLAlchemy with Pydantic Integration.

This module provides a base Data Access Object (DAO) class for common asynchronous
database operations using SQLAlchemy's ORM. It integrates Pydantic for data validation
and transformation, ensuring that all data passed to and from the database conforms
to a defined schema.

Key Components:
---------------
- **FilterCondition**: A wrapper for SQLAlchemy binary expressions that can be used to
  construct dynamic query filters.
- **BaseDAO**: A generic DAO class that provides methods for retrieving, creating,
  and updating database records. All results are transformed into Pydantic models for
  consistency across the application.

Usage Example:
--------------
Assume you have an ORM model `User` (which extends `Base`) and a corresponding Pydantic
schema `UserSchema`. You can define a DAO for the User model as follows:

    from myapp.models import User
    from myapp.schemas import UserSchema
    from myapp.dao import BaseDAO

    class UserDAO(BaseDAO):
        model = User
        schema = UserSchema

Then, you can use the DAO methods like this:

    # Get all users with optional filtering, limit, and offset
    users = await UserDAO.get_all(session, limit=10, offset=0)

    # Get the first user matching a filter condition
    from sqlalchemy import text
    filters = [FilterCondition(User.name == "Alice")]
    user = await UserDAO.get_first(session, filters=filters)

    # Retrieve a user by ID, returning None if not found
    user = await UserDAO.get_one_or_none(session, id=1)

    # Retrieve a user by ID or raise a 404 HTTPException if not found
    user = await UserDAO.get_object_or_404(session, id=1)

    # Create a new user record
    new_user = await UserDAO.create(session, name="Bob", email="bob@example.com")

    # Update an existing user record (using merge)
    updated_user = await UserDAO.update(session, id=1, name="Robert", email="robert@example.com")

Notes:
------
- All models are expected to extend from the SQLAlchemy declarative base (`Base`).
- The DAO methods handle transaction commit/rollback and refresh model instances
  after changes.
- Pydantic's `model_validate` method is used to convert ORM model instances to Pydantic
  models, ensuring that the data is always validated before being used in the application.
"""

from dataclasses import dataclass
from typing import Type, TypeVar

import logfire
from fastapi import HTTPException, status
from fastapi_pagination import LimitOffsetPage
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.engine import Result
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import BinaryExpression

from src.core.engine import Base

T = TypeVar("T", bound=Base)
S = TypeVar("TSchema", bound=BaseModel)


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
        return self.expression


class BaseDAO:
    """
    A generic DAO class for common CRUD operations with SQLAlchemy and Pydantic integration.

    This class provides asynchronous methods for retrieving, creating, and updating
    database records. All records are converted to a Pydantic model using the specified schema.

    Class Attributes:
        model (Type[T]): The SQLAlchemy ORM model class.
        schema (Type[S]): The Pydantic schema class corresponding to the ORM model.
    """

    model: Type[T]
    schema: Type[S]

    @classmethod
    @logfire.instrument()
    async def get_all(
        cls,
        session: AsyncSession,
        limit: int | None = None,
        offset: int | None = None,
        filters: list[FilterCondition] | None = None,
    ) -> list[S]:
        """
        Retrieve all objects from the database, optionally filtered, with pagination.

        Args:
            session (AsyncSession): The active database session.
            limit (int | None): Maximum number of records to return.
            offset (int | None): Number of records to skip.
            filters (list[FilterCondition] | None): A list of FilterCondition instances
                to apply to the query.

        Returns:
            list[S]: A list of Pydantic model instances representing the records.
        """
        statement = select(cls.model).offset(offset).limit(limit)
        if filters:
            for f in filters:
                statement = statement.where(f.to_expression())
        results: Result = await session.execute(statement)
        results = results.scalars().all()
        return [cls.schema.model_validate(result) for result in results]

    @classmethod
    @logfire.instrument()
    async def get_first(
        cls,
        session: AsyncSession,
        filters: list[FilterCondition] | None = None,
    ) -> S | None:
        """
        Retrieve the first record matching the optional filters.

        Args:
            session (AsyncSession): The active database session.
            filters (list[FilterCondition] | None): A list of FilterCondition instances
                to apply to the query.

        Returns:
            S | None: A Pydantic model instance of the first record found or None if no record matches.
        """
        statement = select(cls.model)
        if filters:
            for f in filters:
                statement = statement.where(f.to_expression())
        results: Result = await session.execute(statement)
        results = results.scalars().first()
        if results:
            return cls.schema.model_validate(results)
        return None

    @classmethod
    @logfire.instrument()
    async def get_one_or_none(
        cls,
        session: AsyncSession,
        id: int,
    ) -> S | None:
        """
        Retrieve a record by its primary key.

        Args:
            session (AsyncSession): The active database session.
            id (int): The primary key of the record.

        Returns:
            S | None: A Pydantic model instance if the record is found, otherwise None.
        """
        result = await session.get(cls.model, id)
        if result:
            return cls.schema.model_validate(result)
        return None

    @classmethod
    @logfire.instrument()
    async def get_object_or_404(
        cls,
        session: AsyncSession,
        filters: list[FilterCondition],
    ) -> S | HTTPException:
        """
        Retrieve a record by its primary key or raise an HTTP 404 error if not found.

        Args:
            session (AsyncSession): The active database session.
            id (int): The primary key of the record.

        Returns:
            S: A Pydantic model instance of the found record.

        Raises:
            HTTPException: If no record is found with the given id.
        """
        statement = select(cls.model)
        for f in filters:
            statement = statement.where(f.to_expression())
        results: Result = await session.execute(statement)
        results = results.scalars().first()
        if results:
            return cls.schema.model_validate(results)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    @classmethod
    @logfire.instrument()
    async def create(cls, db: AsyncSession, **object_data: dict) -> S:
        """
        Create a new record in the database.

        This method constructs a new ORM model instance from the provided keyword arguments,
        adds it to the session, commits the transaction, and then transforms the result into
        a Pydantic model.

        Args:
            db (AsyncSession): The active database session.
            **object_data (dict): Key-value pairs corresponding to the model's fields.

        Returns:
            S: A Pydantic model instance representing the newly created record.

        Raises:
            HTTPException: If an IntegrityError occurs (e.g., due to a duplicate record).
        """
        try:
            model_object = cls.model(**object_data)
            db.add(model_object)
            await db.commit()
            await db.refresh(model_object)
            return cls.schema.model_validate(model_object)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Object already exists"
            ) from None

    @classmethod
    @logfire.instrument()
    async def update(cls, db: AsyncSession, **object_data: dict) -> S:
        """
        Update an existing record in the database by merging the provided data.

        This method creates an ORM model instance from the provided keyword arguments,
        merges it into the current session (thereby updating the existing record),
        commits the transaction, and returns the updated record as a Pydantic model.
        The object_data must include the primary key to identify which record to update.

        Args:
            db (AsyncSession): The active database session.
            **object_data (dict): Key-value pairs corresponding to the model's fields,
                including the primary key.

        Returns:
            S: A Pydantic model instance representing the updated record.

        Raises:
            HTTPException: If an IntegrityError occurs during the update operation.
        """
        try:
            model_object = cls.model(**object_data)
            merged_object = await db.merge(model_object)
            await db.commit()
            await db.refresh(merged_object)
            return cls.schema.model_validate(merged_object)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update the object due to integrity constraints.",
            ) from None

    @classmethod
    @logfire.instrument()
    async def get_paginated(
        cls,
        session: AsyncSession,
        filters: list[FilterCondition] | None = None,
    ) -> LimitOffsetPage[T]:
        """
        Retrieve objects from the database with fastapi-pagination integration.

        Pagination (limit/offset) will be applied at the DB level.
        Returned model in items attribute will be transformed to Pydantic model that
         is stated in the router.
        """
        stmt = select(cls.model)
        if filters:
            for f in filters:
                stmt = stmt.where(f.to_expression())
        return await paginate(session, stmt)
