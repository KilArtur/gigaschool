import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.base import Base
from main import app
from endpoints.dependencies import get_db, create_access_token, get_password_hash
from database.repositories import UserRepository, WalletRepository
from core.models.user_role import UserRole


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest_asyncio.fixture
async def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    user_repo = UserRepository(db_session)
    wallet_repo = WalletRepository(db_session)

    hashed_password = get_password_hash("testpassword123")

    user = user_repo.create(
        username="testuser",
        email="test@example.com",
        password_hash=hashed_password,
        balance=0.0,
        role=UserRole.REGULAR,
        is_active=True
    )

    wallet_repo.create(
        user_id=user.id,
        balance=0.0
    )

    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def test_user_with_balance(db_session):
    user_repo = UserRepository(db_session)
    wallet_repo = WalletRepository(db_session)

    hashed_password = get_password_hash("testpassword123")

    user = user_repo.create(
        username="balanceuser",
        email="balance@example.com",
        password_hash=hashed_password,
        balance=100.0,
        role=UserRole.REGULAR,
        is_active=True
    )

    wallet_repo.create(
        user_id=user.id,
        balance=100.0
    )

    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def auth_token(test_user):
    access_token = create_access_token(data={"sub": str(test_user.id)})
    return access_token


@pytest.fixture
def auth_token_with_balance(test_user_with_balance):
    access_token = create_access_token(data={"sub": str(test_user_with_balance.id)})
    return access_token


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def auth_headers_with_balance(auth_token_with_balance):
    return {"Authorization": f"Bearer {auth_token_with_balance}"}