from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    balance: float
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BalanceResponse(BaseModel):
    balance: float


class TopUpRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to add to balance")