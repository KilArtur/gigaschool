from typing import List, Optional
from sqlalchemy.orm import Session
from database.models.query_model import QueryModel
from database.repositories.base_repository import BaseRepository
from core.models.query_status import QueryStatus


class QueryRepository(BaseRepository[QueryModel]):
    def __init__(self, session: Session):
        super().__init__(session, QueryModel)

    def get_by_user_id(self, user_id: int) -> List[QueryModel]:
        return self.session.query(QueryModel).filter(QueryModel.user_id == user_id).order_by(QueryModel.timestamp.desc()).all()

    def get_by_document_id(self, document_id: int) -> List[QueryModel]:
        return self.session.query(QueryModel).filter(QueryModel.document_id == document_id).order_by(QueryModel.timestamp.desc()).all()

    def get_by_status(self, status: QueryStatus) -> List[QueryModel]:
        return self.session.query(QueryModel).filter(QueryModel.status == status).all()

    def get_completed_queries(self) -> List[QueryModel]:
        return self.session.query(QueryModel).filter(QueryModel.status == QueryStatus.COMPLETED).all()

    def get_failed_queries(self) -> List[QueryModel]:
        return self.session.query(QueryModel).filter(QueryModel.status == QueryStatus.FAILED).all()

    def update_status(self, query_id: int, status: QueryStatus) -> Optional[QueryModel]:
        query = self.get_by_id(query_id)
        if query:
            query.status = status
            return self.update(query)
        return None

    def mark_as_completed(self, query_id: int, answer: str, cost: float, input_tokens: int, output_tokens: int) -> Optional[QueryModel]:
        query = self.get_by_id(query_id)
        if query:
            query.status = QueryStatus.COMPLETED
            query.answer = answer
            query.cost = cost
            query.input_tokens = input_tokens
            query.output_tokens = output_tokens
            query.total_tokens = input_tokens + output_tokens
            return self.update(query)
        return None

    def mark_as_failed(self, query_id: int, error_message: str = "") -> Optional[QueryModel]:
        query = self.get_by_id(query_id)
        if query:
            query.status = QueryStatus.FAILED
            if error_message:
                query.answer = f"Error: {error_message}"
            return self.update(query)
        return None