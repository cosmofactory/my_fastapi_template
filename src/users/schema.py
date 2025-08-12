from pydantic import BaseModel, EmailStr

from src.core.schema import STimetampedModel


class UserOutput(BaseModel):
    email: EmailStr


class UserDTO(STimetampedModel):
    id: int
    email: EmailStr
    password: str
    is_superuser: bool
