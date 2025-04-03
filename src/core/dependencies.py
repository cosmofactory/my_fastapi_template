from collections.abc import AsyncGenerator
from typing import Annotated

import httpx
from fastapi import Depends
from fastapi_pagination.limit_offset import LimitOffsetParams

from src.auth.schema import CurrentUser
from src.auth.service import get_current_verified_user

CurrentUserDep = Annotated[CurrentUser, Depends(get_current_verified_user)]


async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient() as client:
        yield client


HttpxDep = Annotated[httpx.AsyncClient, Depends(get_http_client)]


PaginationParams = Annotated[
    LimitOffsetParams,
    Depends(LimitOffsetParams),
]
