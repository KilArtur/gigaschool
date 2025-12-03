from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database.models.user_model import UserModel
from database.repositories import TransactionRepository
from endpoints.dependencies import get_db, get_current_user
from endpoints.models.transaction import TransactionResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/history", response_model=List[TransactionResponse])
def get_transaction_history(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transaction_repo = TransactionRepository(db)
    transactions = transaction_repo.get_by_user_id(current_user.id)

    return [
        TransactionResponse(
            id=t.id,
            user_id=t.user_id,
            amount=t.amount,
            transaction_type=t.transaction_type.value,
            status=t.status.value,
            timestamp=t.timestamp,
            description=t.description,
            related_query_id=t.related_query_id
        )
        for t in transactions
    ]