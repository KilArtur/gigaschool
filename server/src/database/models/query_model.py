from datetime import datetime
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base
from core.models.query_status import QueryStatus


class QueryModel(Base):
    __tablename__ = "queries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, index=True)
    status: Mapped[QueryStatus] = mapped_column(SQLEnum(QueryStatus), default=QueryStatus.PENDING, nullable=False, index=True)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="queries")
    document: Mapped["DocumentModel"] = relationship("DocumentModel", back_populates="queries")
    transactions: Mapped[list["TransactionModel"]] = relationship("TransactionModel", back_populates="related_query", foreign_keys="[TransactionModel.related_query_id]")