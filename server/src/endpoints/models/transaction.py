from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    transaction_type: str
    status: str
    timestamp: datetime
    description: str
    related_query_id: Optional[int]

    class Config:
        from_attributes = True