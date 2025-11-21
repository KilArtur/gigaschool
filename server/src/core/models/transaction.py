from datetime import datetime
from typing import Optional

from core.models.transaction_type import TransactionType
from core.models.transaction_status import TransactionStatus


class Transaction:
    """Финансовая транзакция в системе"""

    def __init__(
        self,
        id: int,
        user_id: int,
        amount: float,
        transaction_type: TransactionType,
        status: TransactionStatus = TransactionStatus.PENDING,
        timestamp: Optional[datetime] = None,
        description: str = "",
        related_query_id: Optional[int] = None,
        processed_by_admin_id: Optional[int] = None
    ):
        self._id: int = id
        self._user_id: int = user_id
        self._amount: float = amount
        self._type: TransactionType = transaction_type
        self._status: TransactionStatus = status
        self._timestamp: datetime = timestamp or datetime.now()
        self._description: str = description
        self._related_query_id: Optional[int] = related_query_id
        self._processed_by_admin_id: Optional[int] = processed_by_admin_id

    # Геттеры
    @property
    def id(self) -> int:
        return self._id

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def type(self) -> TransactionType:
        return self._type

    @property
    def status(self) -> TransactionStatus:
        return self._status

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def description(self) -> str:
        return self._description

    @property
    def related_query_id(self) -> Optional[int]:
        return self._related_query_id

    @property
    def processed_by_admin_id(self) -> Optional[int]:
        return self._processed_by_admin_id

    # Методы обработки
    def process(self) -> None:
        """Помечает транзакцию как завершенную"""
        self._status = TransactionStatus.COMPLETED

    def reject(self, reason: str = "") -> None:
        """
        Отклоняет транзакцию.

        Args:
            reason: Причина отклонения
        """
        self._status = TransactionStatus.REJECTED
        if reason:
            self._description += f" | Rejected: {reason}"

    def is_completed(self) -> bool:
        """Проверяет, завершена ли транзакция"""
        return self._status == TransactionStatus.COMPLETED

    def is_pending(self) -> bool:
        """Проверяет, находится ли транзакция в ожидании"""
        return self._status == TransactionStatus.PENDING

    def is_rejected(self) -> bool:
        """Проверяет, отклонена ли транзакция"""
        return self._status == TransactionStatus.REJECTED
