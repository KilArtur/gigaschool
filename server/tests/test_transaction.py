import pytest
from httpx import AsyncClient
from database.repositories import TransactionRepository
from core.models.transaction_type import TransactionType
from core.models.transaction_status import TransactionStatus


@pytest.mark.asyncio
async def test_get_transaction_history_empty(client: AsyncClient, test_user, auth_headers):
    response = await client.get("/api/v1/transactions/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_transaction_history_after_top_up(client: AsyncClient, test_user, auth_headers):
    await client.post(
        "/api/v1/user/balance/top-up",
        headers=auth_headers,
        json={"amount": 50.0}
    )

    response = await client.get("/api/v1/transactions/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["amount"] == 50.0
    assert data[0]["transaction_type"] == "TOP_UP"
    assert data[0]["status"] == "COMPLETED"
    assert data[0]["user_id"] == test_user.id


@pytest.mark.asyncio
async def test_get_transaction_history_multiple_transactions(client: AsyncClient, test_user, auth_headers):
    await client.post(
        "/api/v1/user/balance/top-up",
        headers=auth_headers,
        json={"amount": 30.0}
    )

    await client.post(
        "/api/v1/user/balance/top-up",
        headers=auth_headers,
        json={"amount": 20.0}
    )

    await client.post(
        "/api/v1/user/balance/top-up",
        headers=auth_headers,
        json={"amount": 50.0}
    )

    response = await client.get("/api/v1/transactions/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    amounts = [t["amount"] for t in data]
    assert 30.0 in amounts
    assert 20.0 in amounts
    assert 50.0 in amounts


@pytest.mark.asyncio
async def test_get_transaction_history_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/transactions/history")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_transaction_has_timestamp(client: AsyncClient, test_user, auth_headers):
    await client.post(
        "/api/v1/user/balance/top-up",
        headers=auth_headers,
        json={"amount": 25.0}
    )

    response = await client.get("/api/v1/transactions/history", headers=auth_headers)
    data = response.json()
    assert len(data) == 1
    assert "timestamp" in data[0]
    assert "id" in data[0]


@pytest.mark.asyncio
async def test_transaction_description_contains_amount(client: AsyncClient, test_user, auth_headers):
    await client.post(
        "/api/v1/user/balance/top-up",
        headers=auth_headers,
        json={"amount": 75.0}
    )

    response = await client.get("/api/v1/transactions/history", headers=auth_headers)
    data = response.json()
    assert "75" in data[0]["description"] or "75.0" in data[0]["description"]


@pytest.mark.asyncio
async def test_user_can_only_see_own_transactions(client: AsyncClient, db_session):
    from endpoints.dependencies import get_password_hash, create_access_token
    from database.repositories import UserRepository, WalletRepository
    from core.models.user_role import UserRole

    user_repo = UserRepository(db_session)
    wallet_repo = WalletRepository(db_session)

    user1 = user_repo.create(
        username="user1",
        email="user1@example.com",
        password_hash=get_password_hash("password123"),
        balance=0.0,
        role=UserRole.REGULAR,
        is_active=True
    )
    wallet_repo.create(user_id=user1.id, balance=0.0)

    user2 = user_repo.create(
        username="user2",
        email="user2@example.com",
        password_hash=get_password_hash("password123"),
        balance=0.0,
        role=UserRole.REGULAR,
        is_active=True
    )
    wallet_repo.create(user_id=user2.id, balance=0.0)

    db_session.commit()

    token1 = create_access_token(data={"sub": str(user1.id)})
    token2 = create_access_token(data={"sub": str(user2.id)})

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    await client.post("/api/v1/user/balance/top-up", headers=headers1, json={"amount": 100.0})
    await client.post("/api/v1/user/balance/top-up", headers=headers2, json={"amount": 200.0})

    response1 = await client.get("/api/v1/transactions/history", headers=headers1)
    response2 = await client.get("/api/v1/transactions/history", headers=headers2)

    data1 = response1.json()
    data2 = response2.json()

    assert len(data1) == 1
    assert len(data2) == 1
    assert data1[0]["amount"] == 100.0
    assert data2[0]["amount"] == 200.0