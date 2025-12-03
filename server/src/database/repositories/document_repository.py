from typing import List, Optional
from sqlalchemy.orm import Session
from database.models.document_model import DocumentModel
from database.repositories.base_repository import BaseRepository
from core.models.document_status import DocumentStatus


class DocumentRepository(BaseRepository[DocumentModel]):
    def __init__(self, session: Session):
        super().__init__(session, DocumentModel)

    def get_by_user_id(self, user_id: int) -> List[DocumentModel]:
        return self.session.query(DocumentModel).filter(DocumentModel.user_id == user_id).order_by(DocumentModel.upload_date.desc()).all()

    def get_by_status(self, status: DocumentStatus) -> List[DocumentModel]:
        return self.session.query(DocumentModel).filter(DocumentModel.status == status).all()

    def get_ready_documents(self) -> List[DocumentModel]:
        return self.session.query(DocumentModel).filter(DocumentModel.status == DocumentStatus.READY).all()

    def get_by_filename(self, filename: str) -> List[DocumentModel]:
        return self.session.query(DocumentModel).filter(DocumentModel.filename.like(f"%{filename}%")).all()

    def update_status(self, document_id: int, status: DocumentStatus) -> Optional[DocumentModel]:
        document = self.get_by_id(document_id)
        if document:
            document.status = status
            return self.update(document)
        return None

    def mark_as_processing(self, document_id: int) -> Optional[DocumentModel]:
        return self.update_status(document_id, DocumentStatus.PROCESSING)

    def mark_as_ready(self, document_id: int, chunk_count: int, page_count: int) -> Optional[DocumentModel]:
        document = self.get_by_id(document_id)
        if document:
            document.status = DocumentStatus.READY
            document.chunk_count = chunk_count
            document.page_count = page_count
            return self.update(document)
        return None

    def mark_as_failed(self, document_id: int) -> Optional[DocumentModel]:
        return self.update_status(document_id, DocumentStatus.FAILED)