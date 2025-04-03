from src.core.base_dao import BaseDAO
from src.users.models import User
from src.users.schema import SUser


class UserDAO(BaseDAO):
    model = User
    schema = SUser
