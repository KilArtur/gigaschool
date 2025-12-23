import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from database.repositories import DocumentRepository
from core.models.document_status import DocumentStatus


@pytest.fixture
def test_document(db_session, test_user_with_balance):
    document_repo = DocumentRepository(db_session)

    document = document_repo.create(
        user_id=test_user_with_balance.id,
        filename="test_document.pdf",
        file_path="/tmp/test_document.pdf",
        status=DocumentStatus.READY,
        chunk_count=10,
        page_count=5,
        file_size_mb=1.5
    )

    db_session.commit()
    db_session.refresh(document)

    return document


@pytest.mark.asyncio
@patch('endpoints.api.query.RabbitMQService')
async def test_create_query_success(mock_rabbitmq_class, client: AsyncClient, test_user_with_balance, test_document, auth_headers_with_balance):
    mock_rabbitmq = AsyncMock()
    mock_rabbitmq.publish_query_task = AsyncMock()
    mock_rabbitmq_class.return_value = mock_rabbitmq

    response = await client.post(
        "/api/v1/queries/",
        headers=auth_headers_with_balance,
        json={
            "document_id": test_document.id,
            "question": "What is the main topic of the document?"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["question"] == "What is the main topic of the document?"
    assert data["document_id"] == test_document.id
    assert data["user_id"] == test_user_with_balance.id
    assert data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_create_query_document_not_found(client: AsyncClient, test_user_with_balance, auth_headers_with_balance):
    response = await client.post(
        "/api/v1/queries/",
        headers=auth_headers_with_balance,
        json={
            "document_id": 99999,
            "question": "What is this?"
        }
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
@patch('endpoints.api.query.RabbitMQService')
async def test_create_query_insufficient_balance(mock_rabbitmq_class, client: AsyncClient, test_user, test_document, auth_headers, db_session):
    test_user.balance = -10.0
    db_session.commit()

    response = await client.post(
        "/api/v1/queries/",
        headers=auth_headers,
        json={
            "document_id": test_document.id,
            "question": "What is this?"
        }
    )

    assert response.status_code == 402
    assert "insufficient balance" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_query_document_not_ready(client: AsyncClient, test_user_with_balance, auth_headers_with_balance, db_session):
    document_repo = DocumentRepository(db_session)

    document = document_repo.create(
        user_id=test_user_with_balance.id,
        filename="processing.pdf",
        file_path="/tmp/processing.pdf",
        status=DocumentStatus.PROCESSING,
        chunk_count=0,
        page_count=0,
        file_size_mb=1.0
    )

    db_session.commit()

    response = await client.post(
        "/api/v1/queries/",
        headers=auth_headers_with_balance,
        json={
            "document_id": document.id,
            "question": "What is this?"
        }
    )

    assert response.status_code == 400
    assert "not ready" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_query_unauthorized(client: AsyncClient, test_document):
    response = await client.post(
        "/api/v1/queries/",
        json={
            "document_id": test_document.id,
            "question": "What is this?"
        }
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_query_wrong_user_document(client: AsyncClient, test_user, auth_headers, db_session):
    from endpoints.dependencies import get_password_hash, create_access_token
    from database.repositories import UserRepository, WalletRepository
    from core.models.user_role import UserRole

    user_repo = UserRepository(db_session)
    wallet_repo = WalletRepository(db_session)

    other_user = user_repo.create(
        username="otheruser",
        email="other@example.com",
        password_hash=get_password_hash("password123"),
        balance=100.0,
        role=UserRole.REGULAR,
        is_active=True
    )
    wallet_repo.create(user_id=other_user.id, balance=100.0)

    document_repo = DocumentRepository(db_session)
    other_document = document_repo.create(
        user_id=other_user.id,
        filename="other.pdf",
        file_path="/tmp/other.pdf",
        status=DocumentStatus.READY,
        chunk_count=5,
        page_count=3,
        file_size_mb=1.0
    )

    db_session.commit()

    response = await client.post(
        "/api/v1/queries/",
        headers=auth_headers,
        json={
            "document_id": other_document.id,
            "question": "What is this?"
        }
    )

    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


@pytest.mark.asyncio
@patch('endpoints.api.query.RabbitMQService')
async def test_get_query_history_empty(mock_rabbitmq_class, client: AsyncClient, test_user_with_balance, auth_headers_with_balance):
    response = await client.get("/api/v1/queries/history", headers=auth_headers_with_balance)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
@patch('endpoints.api.query.RabbitMQService')
async def test_get_query_history_after_query(mock_rabbitmq_class, client: AsyncClient, test_user_with_balance, test_document, auth_headers_with_balance):
    mock_rabbitmq = AsyncMock()
    mock_rabbitmq.publish_query_task = AsyncMock()
    mock_rabbitmq_class.return_value = mock_rabbitmq

    await client.post(
        "/api/v1/queries/",
        headers=auth_headers_with_balance,
        json={
            "document_id": test_document.id,
            "question": "What is the main topic?"
        }
    )

    response = await client.get("/api/v1/queries/history", headers=auth_headers_with_balance)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["question"] == "What is the main topic?"


@pytest.mark.asyncio
@patch('endpoints.api.query.RabbitMQService')
async def test_get_specific_query(mock_rabbitmq_class, client: AsyncClient, test_user_with_balance, test_document, auth_headers_with_balance):
    mock_rabbitmq = AsyncMock()
    mock_rabbitmq.publish_query_task = AsyncMock()
    mock_rabbitmq_class.return_value = mock_rabbitmq

    create_response = await client.post(
        "/api/v1/queries/",
        headers=auth_headers_with_balance,
        json={
            "document_id": test_document.id,
            "question": "What is this about?"
        }
    )

    query_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/queries/{query_id}", headers=auth_headers_with_balance)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == query_id
    assert data["question"] == "What is this about?"


@pytest.mark.asyncio
async def test_get_query_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/queries/1")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_query_not_found(client: AsyncClient, test_user_with_balance, auth_headers_with_balance):
    response = await client.get("/api/v1/queries/99999", headers=auth_headers_with_balance)
    assert response.status_code == 404