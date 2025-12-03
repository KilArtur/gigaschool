from typing import List, Optional
from sqlalchemy.orm import Session
from database.models.transaction_model import TransactionModel
from database.repositories.base_repository import BaseRepository
from core.models.transaction_type import TransactionType
from core.models.transaction_status import TransactionStatus


class TransactionRepository(BaseRepository[TransactionModel]):
    def __init__(self, session: Session):
        super().__init__(session, TransactionModel)

    def get_by_user_id(self, user_id: int) -> List[TransactionModel]:
        return self.session.query(TransactionModel).filter(TransactionModel.user_id == user_id).order_by(TransactionModel.timestamp.desc()).all()

    def get_by_type(self, transaction_type: TransactionType) -> List[TransactionModel]:
        return self.session.query(TransactionModel).filter(TransactionModel.transaction_type == transaction_type).all()

    def get_by_status(self, status: TransactionStatus) -> List[TransactionModel]:
        return self.session.query(TransactionModel).filter(TransactionModel.status == status).all()

    def get_by_query_id(self, query_id: int) -> List[TransactionModel]:
        return self.session.query(TransactionModel).filter(TransactionModel.related_query_id == query_id).all()

    def get_pending_transactions(self) -> List[TransactionModel]:
        return self.session.query(TransactionModel).filter(TransactionModel.status == TransactionStatus.PENDING).all()

    def mark_completed(self, transaction_id: int) -> Optional[TransactionModel]:
        transaction = self.get_by_id(transaction_id)
        if transaction:
            transaction.status = TransactionStatus.COMPLETED
            return self.update(transaction)
        return None

    def mark_rejected(self, transaction_id: int, reason: str = "") -> Optional[TransactionModel]:
        transaction = self.get_by_id(transaction_id)
        if transaction:
            transaction.status = TransactionStatus.REJECTED
            if reason:
                transaction.description += f" | Rejected: {reason}"
            return self.update(transaction)
        return None