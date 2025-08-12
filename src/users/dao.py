from src.core.base_dao import BaseDAO
from src.users.models import User


class UserDAO(BaseDAO):
    model = User
