from enum import Enum


class QueryStatus(Enum):
    """Статусы запроса"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
