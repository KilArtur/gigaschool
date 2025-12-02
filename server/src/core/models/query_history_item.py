from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from core.models.query_status import QueryStatus


@dataclass
class QueryHistoryItem:
    id: int
    user_id: int
    document_id: int
    question: str
    answer: Optional[str]
    cost: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    timestamp: datetime
    status: QueryStatus

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "document_id": self.document_id,
            "question": self.question,
            "answer": self.answer,
            "cost": self.cost,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value
        }