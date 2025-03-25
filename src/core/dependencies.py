from typing import Annotated

from fastapi import Depends

from src.auth.schema import CurrentUser
from src.auth.service import get_current_verified_user

CurrentUserDep = Annotated[CurrentUser, Depends(get_current_verified_user)]
