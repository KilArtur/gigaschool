from enum import Enum


class DocumentStatus(Enum):
    """Статусы документа"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
