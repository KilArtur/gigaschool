from enum import Enum


class TransactionStatus(Enum):
    """Статусы транзакций"""
    PENDING = "pending"
    COMPLETED = "completed"
    REJECTED = "rejected"
