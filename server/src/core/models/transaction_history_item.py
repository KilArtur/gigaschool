from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from core.models.transaction_type import TransactionType
from core.models.transaction_status import TransactionStatus


@dataclass
class TransactionHistoryItem:
    id: int
    user_id: int
    amount: float
    transaction_type: TransactionType
    status: TransactionStatus
    timestamp: datetime
    description: str = ""
    related_query_id: Optional[int] = None
    processed_by_admin_id: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "type": self.transaction_type.value,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "related_query_id": self.related_query_id,
            "processed_by_admin_id": self.processed_by_admin_id
        }