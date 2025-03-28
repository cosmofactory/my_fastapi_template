from fastapi import HTTPException
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from src.auth.service import authenticate_user, create_tokens, get_current_user
from src.core.engine import async_session_maker


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        """
        Login form for SQL Admin.

        Get the user from the database and check if the user is an admin.
        In case of success, create a token and save it to the session.
        """
        async with async_session_maker() as session:
            form = await request.form()
            email, password = form["username"], form["password"]
            try:
                user = await authenticate_user(session, email, password)
                # TODO add admin check
            except HTTPException:
                return False
            tokens = await create_tokens(session, user)
            request.session.update({"token": tokens.get("access_token")})

        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """
        Check if the user is authenticated and is an admin.
        """
        if token := request.session.get("token"):
            async with async_session_maker() as db:
                try:
                    if user := await get_current_user(token, db):
                        if user.is_superuser:
                            return True
                except HTTPException:
                    pass
        return False


authentication_backend = AdminAuth(secret_key="...")
