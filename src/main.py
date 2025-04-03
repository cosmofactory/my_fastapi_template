import logfire
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from sqladmin import Admin

from src.admin.auth import authentication_backend
from src.admin.generations import GenerationAdmin
from src.admin.users import UserAdmin
from src.auth.router import router as auth_router
from src.core.engine import async_engine
from src.generations.router import router as generations_router
from src.settings import settings
from src.users.router import router as users_router

app = FastAPI()


logfire.configure(
    inspect_arguments=True,
    service_name=settings.SERVICE_NAME,
    metrics=False,
    environment=settings.ENV,
)
logfire.instrument_fastapi(app)


app.include_router(users_router)
app.include_router(auth_router)
app.include_router(generations_router)

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

# SQLAdmin config
admin = Admin(
    app,
    engine=async_engine,
    title="MOI Admin",
    authentication_backend=authentication_backend,
)

admin.add_view(UserAdmin)
admin.add_view(GenerationAdmin)
