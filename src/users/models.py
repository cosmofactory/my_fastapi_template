from pydantic import EmailStr
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.models import TimeStampedModel


class User(TimeStampedModel):
    """User model."""

    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[EmailStr] = mapped_column(String(256), unique=True)
    password: Mapped[str]
    is_superuser: Mapped[bool] = mapped_column(default=False)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r})"

    def __str__(self) -> str:
        return f"User(id={self.id}, email={self.email})"
