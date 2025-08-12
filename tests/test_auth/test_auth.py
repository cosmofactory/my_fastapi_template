from httpx import AsyncClient


async def test_profile_me(ac_client: AsyncClient):
    """Test the profile me endpoint is accessable for verified user."""
    response = await ac_client.get("/users/profile/me")
    data = response.json()

    assert response.status_code == 200
    assert data["email"] == "test@user.com"
    assert data.get("password") is None
