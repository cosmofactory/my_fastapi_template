import pytest
from fastapi import status
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel
from sqlmodel.pool import StaticPool

from src.auth.service import get_password_hash
from src.core.session import get_async_session
from src.main import app
from src.users.models import User

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(name="session", scope="session")
async def session_fixture():
    engine = create_async_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    async_session_maker = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    def get_session_override():
        return session

    app.dependency_overrides[get_async_session] = get_session_override
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="session")
async def ac():
    """Create an AsyncClient instance."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as ac:
        yield ac


@pytest.fixture(scope="session")
async def ac_client(session: Session):
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


@pytest.fixture(scope="session")
async def ac_client_not_verified(session: Session):
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
