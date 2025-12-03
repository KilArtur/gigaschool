from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.repositories import UserRepository, WalletRepository
from endpoints.dependencies import (
    get_db,
    verify_password,
    get_password_hash,
    create_access_token
)
from endpoints.models.auth import RegisterRequest, LoginRequest, TokenResponse
from core.models.user_role import UserRole

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    wallet_repo = WalletRepository(db)

    if user_repo.get_by_username(request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    if user_repo.get_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = get_password_hash(request.password)

    user = user_repo.create(
        username=request.username,
        email=request.email,
        password_hash=hashed_password,
        balance=0.0,
        role=UserRole.REGULAR,
        is_active=True
    )

    wallet_repo.create(
        user_id=user.id,
        balance=0.0
    )

    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    user = user_repo.get_by_username(request.username)

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(access_token=access_token)