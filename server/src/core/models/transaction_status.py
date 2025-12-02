from enum import Enum


class TransactionStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    REJECTED = "rejected"
