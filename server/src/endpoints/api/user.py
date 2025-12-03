from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.models.user_model import UserModel
from database.repositories import UserRepository, WalletRepository, TransactionRepository
from endpoints.dependencies import get_db, get_current_user
from endpoints.models.user import UserResponse, BalanceResponse, TopUpRequest
from core.models.transaction_type import TransactionType
from core.models.transaction_status import TransactionStatus

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: UserModel = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        balance=current_user.balance,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.get("/balance", response_model=BalanceResponse)
def get_balance(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    wallet_repo = WalletRepository(db)
    wallet = wallet_repo.get_by_user_id(current_user.id)

    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )

    return BalanceResponse(balance=wallet.balance)


@router.post("/balance/top-up", response_model=BalanceResponse)
def top_up_balance(
    request: TopUpRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    wallet_repo = WalletRepository(db)
    transaction_repo = TransactionRepository(db)
    user_repo = UserRepository(db)

    wallet = wallet_repo.get_by_user_id(current_user.id)

    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )

    wallet_repo.add_balance(wallet.id, request.amount)

    user_repo.update_balance(current_user.id, wallet.balance + request.amount)

    transaction_repo.create(
        user_id=current_user.id,
        amount=request.amount,
        transaction_type=TransactionType.TOP_UP,
        status=TransactionStatus.COMPLETED,
        description=f"Balance top-up: {request.amount}"
    )

    wallet = wallet_repo.get_by_id(wallet.id)

    return BalanceResponse(balance=wallet.balance)