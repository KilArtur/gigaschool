from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    file_path: str
    upload_date: datetime
    status: str
    chunk_count: int
    page_count: int
    file_size_mb: float

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    status: str
    message: str