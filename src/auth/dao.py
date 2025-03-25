from src.auth.models import RefreshToken
from src.core.base_dao import BaseDAO


class RefreshTokenDAO(BaseDAO):
    model = RefreshToken
