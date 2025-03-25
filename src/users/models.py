from sqlmodel import Field

from src.core.models import TimeStampedModel


class User(TimeStampedModel, table=True):
    email: str = Field(unique=True)
    password: str
    is_superuser: bool = Field(default=False)
    is_verified: bool = Field(default=False)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r})"

    def __str__(self) -> str:
        return f"User(id={self.id}, email={self.email})"
