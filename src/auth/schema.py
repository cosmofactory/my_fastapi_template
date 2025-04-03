from pydantic import BaseModel, EmailStr

from src.core.schema import OrmModel


class UserRegisterInput(OrmModel):
    """User registration schema."""

    email: EmailStr
    password: str


class UserLoginOutput(OrmModel):
    """User login schema."""

    id: int
    email: EmailStr
    is_verified: bool


class CurrentUser(UserLoginOutput):
    is_superuser: bool


class STokens(BaseModel):
    """Tokens schema."""

    access_token: str
    refresh_token: str


class TokenData(BaseModel):
    """Token data schema."""

    email: str


class TokenOutput(BaseModel):
    """Token pair schema."""

    access_token: str
    refresh_token: str | None
    token_type: str
    user_data: UserLoginOutput
