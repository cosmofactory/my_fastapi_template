from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.schema import TokenOutput, UserRegisterInput
from src.auth.service import (
    login_user,
    logout_user,
    refresh_user_token,
    register_user,
    verify_email,
)
from src.core.schema import ErrorResponse
from src.core.session import SessionDep

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "User with this email already exists",
        }
    },
)
async def register_user_handler(
    user_data: UserRegisterInput,
    session: SessionDep,
    background_tasks: BackgroundTasks,
) -> None:
    await register_user(user_data, session, background_tasks)


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Invalid credentials",
        }
    },
    response_model=TokenOutput,
)
async def login_handler(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    session: SessionDep,
) -> TokenOutput:
    return await login_user(session, form_data, response)


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Invalid credentials",
        }
    },
    response_model=TokenOutput,
)
async def refresh(request: Request, response: Response, session: SessionDep) -> TokenOutput:
    return await refresh_user_token(session, request, response)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    logout_user(response)


@router.get("/verify")
async def verify_email_handler(token: str, session: SessionDep) -> None:
    await verify_email(token, session)
    return Response(status_code=status.HTTP_200_OK)
