import datetime
from typing import Annotated

import jwt
import logfire
from fastapi import BackgroundTasks, Depends, Request, Response, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schema import (
    CurrentUser,
    TokenData,
    TokenOutput,
    UserLoginOutput,
    UserRegisterInput,
)
from src.core.base_dao import FilterCondition
from src.core.exceptions import (
    CouldNotValidateCredentialsException,
    InvalidCredentialsException,
    InvalidRefreshTokenException,
    InvalidTokenPayloadException,
    InvalidTokenTypeException,
    TokenExpiredException,
    UserExistsException,
    UserNotFoundException,
    VerificationRequiredException,
)
from src.core.session import get_async_session
from src.emails.service import render_verification_email, send_email
from src.settings import settings
from src.users.dao import UserDAO
from src.users.models import User
from src.users.schema import SUser

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_password_hash(password: str) -> str:
    """Hash given password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """Verify the given password and existing password."""
    if not hashed_password:
        raise InvalidCredentialsException
    return pwd_context.verify(plain_password, hashed_password)


async def check_user_exists(session: AsyncSession, user_data: UserRegisterInput) -> None:
    """Check if the user with the provided email exists and hash the password."""
    check_existing_user = await UserDAO.get_first(
        session, filters=[FilterCondition(User.email == user_data.email)]
    )
    if check_existing_user:
        raise UserExistsException


async def authenticate_user(session: AsyncSession, email, password) -> UserLoginOutput:
    """Check if the user with the provided email and password exists."""
    user: User = await UserDAO.get_first(session, filters=[FilterCondition(User.email == email)])
    logfire.info("User", user=user)
    if not user or not verify_password(password, user.password):
        raise InvalidCredentialsException
    return UserLoginOutput.model_validate(user)


def create_access_token(data: dict, expires_delta: datetime.timedelta):
    """Create access token with the given data and expiration time."""
    to_encode = data.copy()
    if expires_delta is not None:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.auth.JWT_SECRET_KEY, algorithm=settings.auth.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: datetime.timedelta):
    """Create refresh token with the given data and expiration time."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.auth.JWT_SECRET_KEY, algorithm=settings.auth.ALGORITHM
    )
    return encoded_jwt


async def create_tokens(user: UserLoginOutput) -> dict:
    """
    Call the create_access_token and create_refresh_token.

    Save the refresh token to the database for further use.
    """
    access_token_expires = datetime.timedelta(minutes=settings.auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    refresh_token_expires = datetime.timedelta(days=settings.auth.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user.email}, expires_delta=refresh_token_expires
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "access_token_expires": access_token_expires.total_seconds(),
        "refresh_token_expires": refresh_token_expires.total_seconds(),
    }


async def set_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    access_token_expires: float,
    refresh_token_expires: float,
) -> None:
    """Set the access token and refresh token as cookies."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.SAMESITE_VALUE,
        max_age=int(access_token_expires),
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.SAMESITE_VALUE,
        max_age=int(refresh_token_expires),
    )


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], session=Depends(get_async_session)
) -> CurrentUser:
    """Get the current user with the given token."""
    credentials_exception = CouldNotValidateCredentialsException
    try:
        payload = jwt.decode(
            token, settings.auth.JWT_SECRET_KEY, algorithms=[settings.auth.ALGORITHM]
        )
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except InvalidTokenError:
        raise credentials_exception from None
    user: SUser = await UserDAO.get_first(
        session, filters=[FilterCondition(User.email == token_data.email)]
    )
    if not user:
        raise credentials_exception
    return CurrentUser.model_validate(user)


async def get_current_verified_user(
    current_user: Annotated[CurrentUser, Security(get_current_user)],
) -> CurrentUser:
    """Get current user with extra scope."""
    if current_user.is_verified is False:
        raise VerificationRequiredException
    return current_user


async def register_user(
    user_data: UserRegisterInput,
    session: AsyncSession,
    background_tasks: BackgroundTasks,
):
    """
    Register a new user.

    1. Check for if user already exists, throw HTTP 409 in that case.
    2. Hash user password
    3. Create user in database.
    4. Create email verification token.
    5. Send verification email.
    """
    await check_user_exists(session, user_data)
    hashed_password = get_password_hash(user_data.password)
    await UserDAO.create(session, email=user_data.email, password=hashed_password)
    token = create_email_verification_token(user_data.email)
    background_tasks.add_task(send_verification_email, user_data.email, token)


async def login_user(
    session: AsyncSession,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
) -> TokenOutput:
    """
    Log in the user.

    If the user with the provided email and password exists, create access and refresh tokens.
    Refresh token will be stored in database.
    Both access and refresh tokens will be added to cookies.
    Return token values.
    """
    user = await authenticate_user(session, form_data.username, form_data.password)
    tokens = await create_tokens(user)
    await set_cookies(
        response,
        tokens["access_token"],
        tokens["refresh_token"],
        tokens["access_token_expires"],
        tokens["refresh_token_expires"],
    )
    return TokenOutput(**tokens, user_data=user)


def logout_user(response: Response) -> None:
    """
    Log out the user.

    Remove access and refresh tokens from cookies.
    """
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


async def refresh_user_token(
    session: AsyncSession, request: Request, response: Response
) -> TokenOutput:
    """
    Refresh access token.
    Check if the refresh token is valid and exists in cookies.
    If the refresh token is valid, create new access and refresh tokens.
    Both access and refresh tokens will be added to cookies.
    Return token values.
    """
    wrong_credentials = InvalidRefreshTokenException
    if refresh_token := request.cookies.get("refresh_token"):
        try:
            payload = jwt.decode(
                refresh_token,
                settings.auth.JWT_SECRET_KEY,
                algorithms=[settings.auth.ALGORITHM],
            )
            email: str = payload.get("sub")
        except InvalidTokenError:
            raise wrong_credentials from None
        user = await UserDAO.get_first(session, filters=[FilterCondition(User.email == email)])
        new_tokens = await create_tokens(user)
        await set_cookies(
            response,
            new_tokens.get("access_token"),
            new_tokens.get("refresh_token"),
            new_tokens.get("access_token_expires"),
            new_tokens.get("refresh_token_expires"),
        )
        return TokenOutput(**new_tokens, user_data=user)
    else:
        raise wrong_credentials


def create_email_verification_token(
    email: str,
    expires_delta: datetime.timedelta = datetime.timedelta(
        hours=settings.auth.EMAIL_VERIFICATION_EXPIRATION_HOURS
    ),
) -> str:
    """Create a token for email verification."""
    payload = {
        "sub": email,
        "verify": True,
        "exp": datetime.datetime.now(datetime.timezone.utc) + expires_delta,
    }
    return jwt.encode(payload, settings.auth.JWT_SECRET_KEY, algorithm=settings.auth.ALGORITHM)


async def send_verification_email(email: str, token: str) -> None:
    """Send email with the verification token."""
    verification_link = f"{settings.VEIRIFICATION_URL}{token}"
    email_body = render_verification_email(email, verification_link)
    await send_email(email, f"Email Verification for {settings.PROJECT_NAME}", email_body)


async def verify_email(token: str, session: AsyncSession) -> None:
    """
    Verify the email with the given token.

    Update user in database in case of successful verification.
    """
    try:
        payload = jwt.decode(
            token, settings.auth.JWT_SECRET_KEY, algorithms=[settings.auth.ALGORITHM]
        )
        if not payload.get("verify"):
            raise InvalidTokenTypeException
        email = payload.get("sub")
        if email is None:
            raise InvalidTokenPayloadException
    except jwt.ExpiredSignatureError as e:
        raise TokenExpiredException from e
    except jwt.InvalidTokenError as e:
        raise InvalidTokenTypeException from e

    user: SUser = await UserDAO.get_first(session, filters=[FilterCondition(User.email == email)])
    if not user:
        raise UserNotFoundException

    user.is_verified = True
    await UserDAO.update(session, user)
