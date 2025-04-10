import pytest
from fastapi import status
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.auth.service import get_password_hash
from src.core.engine import Base
from src.core.session import get_async_session
from src.main import app
from src.users.models import User

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest.fixture(scope="function")
async def session():
    async with engine.connect() as connection:
        transaction = await connection.begin()
        async with SessionLocal(bind=connection) as session:
            yield session
        await transaction.rollback()


@pytest.fixture(autouse=True)
async def override_db_session(session: AsyncSession):
    async def _get_test_db():
        yield session

    app.dependency_overrides[get_async_session] = _get_test_db
    yield
    app.dependency_overrides.pop(get_async_session, None)


@pytest.fixture(scope="function")
async def ac():
    """Create an AsyncClient instance."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as ac:
        yield ac


@pytest.fixture(scope="function")
async def ac_client(session: AsyncSession):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as client:
        password = get_password_hash("client_password1")
        user = User(email="test@user.com", password=password, is_superuser=False, is_verified=True)
        session.add(user)
        await session.commit()
        response = await client.post(
            "/auth/login",
            data={
                "username": "test@user.com",
                "password": "client_password1",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        access_token = response.json()["access_token"]
        client.headers.update({"Authorization": f"Bearer {access_token}"})
        assert response.status_code == status.HTTP_200_OK
        assert client.cookies.get("access_token") is not None
        assert client.cookies.get("refresh_token") is not None
        client.user = user
        yield client


@pytest.fixture(scope="function")
async def ac_client_not_verified(session: AsyncSession):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as client:
        password = get_password_hash("client_password1")
        user = User(email="unverified@user.com", password=password, is_superuser=False)
        session.add(user)
        await session.commit()
        response = await client.post(
            "/auth/login",
            data={
                "username": "unverified@user.com",
                "password": "client_password1",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        access_token = response.json()["access_token"]
        client.headers.update({"Authorization": f"Bearer {access_token}"})
        assert response.status_code == status.HTTP_200_OK
        assert client.cookies.get("access_token") is not None
        assert client.cookies.get("refresh_token") is not None
        client.user = user
        yield client
