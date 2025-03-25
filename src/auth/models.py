from datetime import datetime

from sqlmodel import Field

from src.core.models import TimeStampedModel


class RefreshToken(TimeStampedModel, table=True):
    token: str
    expires_at: datetime
    revoked: bool = False

    user_id: int = Field(foreign_key="user.id")

    def __repr__(self) -> str:
        return f"RefreshToken(id={self.id!r}, related_user={self.user_id!r})"

    def __str__(self) -> str:
        return f"RefreshToken(id={self.id}, related_user={self.user_id})"
