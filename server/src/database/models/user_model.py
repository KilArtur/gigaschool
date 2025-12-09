from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base
from core.models.user_role import UserRole


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.REGULAR, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    wallet: Mapped["WalletModel"] = relationship("WalletModel", back_populates="user", uselist=False, cascade="all, delete-orphan")
    transactions: Mapped[list["TransactionModel"]] = relationship("TransactionModel", back_populates="user", cascade="all, delete-orphan", foreign_keys="[TransactionModel.user_id]")
    documents: Mapped[list["DocumentModel"]] = relationship("DocumentModel", back_populates="user", cascade="all, delete-orphan")
    queries: Mapped[list["QueryModel"]] = relationship("QueryModel", back_populates="user", cascade="all, delete-orphan")