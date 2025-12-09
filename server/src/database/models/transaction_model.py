from datetime import datetime
from sqlalchemy import Integer, Float, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base
from core.models.transaction_type import TransactionType
from core.models.transaction_status import TransactionStatus


class TransactionModel(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(SQLEnum(TransactionType), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    related_query_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("queries.id", ondelete="SET NULL"), nullable=True)
    processed_by_admin_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="transactions", foreign_keys=[user_id])
    related_query: Mapped["QueryModel"] = relationship("QueryModel", back_populates="transactions", foreign_keys=[related_query_id])