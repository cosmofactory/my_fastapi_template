from fastapi import APIRouter, status

from src.auth.schema import CurrentUser
from src.core.dependencies import CurrentUserDep
from src.core.schema import ErrorResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/profile/me",
    response_model=CurrentUser,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "User not found",
        }
    },
)
async def get_user_handler(current_user: CurrentUserDep) -> CurrentUser:
    return current_user
