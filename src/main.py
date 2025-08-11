from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

import logfire
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from sqladmin import Admin

from src.admin.auth import authentication_backend
from src.admin.users import UserAdmin
from src.auth.router import router as auth_router
from src.core.engine import Database
from src.settings import settings
from src.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Manage application lifespan events.

    Sets up database connection on startup and cleans up on shutdown.
    AsyncExitStack is used to manage connection context and gracefully
    close sessions.
    """
    async with AsyncExitStack() as stack:
        # === Postgres Client Initialization ===
        database = Database(database_url=settings.database.DATABASE_URL)
        app.state.postgres_db = database
        stack.push_async_callback(database.dispose)

        yield


app = FastAPI(lifespan=lifespan)


logfire.configure(
    inspect_arguments=True,
    service_name=settings.SERVICE_NAME,
    metrics=False,
    environment=settings.ENV,
)
logfire.instrument_fastapi(app)


app.include_router(users_router)
app.include_router(auth_router)

origins = [
    "http://localhost:3000",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_pagination(app)

admin = Admin(
    app,
    engine=app.state.postgres_db._engine,
    title="Internal admin",
    authentication_backend=authentication_backend,
)
admin.add_view(UserAdmin)
