import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, test_user, auth_headers):
    response = await client.get("/api/v1/user/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["balance"] == 0.0
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/user/me")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    headers = {"Authorization": "Bearer invalid_token"}
    response = await client.get("/api/v1/user/me", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_balance(client: AsyncClient, test_user, auth_headers):
    response = await client.get("/api/v1/user/balance", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["balance"] == 0.0


@pytest.mark.asyncio
async def test_get_balance_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/user/balance")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_top_up_balance_success(client: AsyncClient, test_user, auth_headers):
    response = await client.post(
        "/api/v1/user/balance/top-up",
        headers=auth_headers,
        json={"amount": 50.0}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["balance"] == 50.0


@pytest.mark.asyncio
async def test_top_up_balance_multiple_times(client: AsyncClient, test_user, auth_headers):
    response1 = await client.post(
        "/api/v1/user/balance/top-up",
        headers=auth_headers,
        json={"amount": 30.0}
    )
    assert response1.status_code == 200
    assert response1.json()["balance"] == 30.0

    response2 = await client.post(
        "/api/v1/user/balance/top-up",
        headers=auth_headers,
        json={"amount": 20.0}
    )
    assert response2.status_code == 200
    assert response2.json()["balance"] == 50.0


@pytest.mark.asyncio
async def test_top_up_balance_invalid_amount(client: AsyncClient, test_user, auth_headers):
    response = await client.post(
        "/api/v1/user/balance/top-up",
        headers=auth_headers,
        json={"amount": -10.0}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_top_up_balance_zero_amount(client: AsyncClient, test_user, auth_headers):
    response = await client.post(
        "/api/v1/user/balance/top-up",
        headers=auth_headers,
        json={"amount": 0.0}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_top_up_balance_unauthorized(client: AsyncClient):
    response = await client.post(
        "/api/v1/user/balance/top-up",
        json={"amount": 50.0}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_balance_persists_after_top_up(client: AsyncClient, test_user, auth_headers):
    await client.post(
        "/api/v1/user/balance/top-up",
        headers=auth_headers,
        json={"amount": 100.0}
    )

    response = await client.get("/api/v1/user/balance", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["balance"] == 100.0

    response = await client.get("/api/v1/user/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["balance"] == 100.0