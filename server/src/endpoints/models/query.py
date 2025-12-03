from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class QueryRequest(BaseModel):
    document_id: int
    question: str = Field(..., min_length=1, max_length=1000)


class QueryResponse(BaseModel):
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
    status: str

    class Config:
        from_attributes = True