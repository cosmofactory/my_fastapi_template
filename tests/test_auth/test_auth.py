import datetime

import jwt
import pytest
from fastapi import status
from httpx import AsyncClient

from src.auth.service import create_email_verification_token
from src.settings import settings


async def test_profile_me(ac_client: AsyncClient):
    """Test the profile me endpoint is accessable for verified user."""
    response = await ac_client.get("/users/profile/me")
    data = response.json()

    assert response.status_code == 200
    assert data["email"] == "test@user.com"
    assert data.get("password") is None


async def test_profile_me_not_verified(ac_client_not_verified: AsyncClient):
    """Test the profile me endpoint is not accessable for unverified user."""
    response = await ac_client_not_verified.get("/users/profile/me")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    "email, expires_delta",
    [
        ("test@example.com", datetime.timedelta(hours=1)),
        ("user@domain.com", datetime.timedelta(hours=2)),
        ("another@example.com", datetime.timedelta(hours=3)),
    ],
)
def test_create_email_verification_token(email, expires_delta):
    token = create_email_verification_token(email, expires_delta)
    payload = jwt.decode(token, settings.auth.JWT_SECRET_KEY, algorithms=[settings.auth.ALGORITHM])

    assert payload.get("sub") == email
    assert payload.get("verify") is True

    now = datetime.datetime.now(datetime.timezone.utc)
    token_exp = datetime.datetime.fromtimestamp(payload.get("exp"), tz=datetime.timezone.utc)

    expected_exp = now + expires_delta
    time_difference = abs((token_exp - expected_exp).total_seconds())
    assert time_difference < 2, f"Expiration delta {time_difference} exceeded allowed tolerance"
