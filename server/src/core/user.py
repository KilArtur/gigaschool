from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from core.models.user_role import UserRole

if TYPE_CHECKING:
    from core.query import Query


class User:

    def __init__(
        self,
        id: int,
        username: str,
        email: str,
        password_hash: str,
        balance: float = 0.0,
        role: UserRole = UserRole.REGULAR,
        created_at: Optional[datetime] = None,
        is_active: bool = True
    ):
        self._id: int = id
        self._username: str = username
        self._email: str = email
        self._password_hash: str = password_hash
        self._balance: float = balance
        self._role: UserRole = role
        self._created_at: datetime = created_at or datetime.now()
        self._is_active: bool = is_active

    @property
    def id(self) -> int:
        return self._id

    @property
    def username(self) -> str:
        return self._username

    @property
    def email(self) -> str:
        return self._email

    @property
    def balance(self) -> float:
        return self._balance

    @property
    def role(self) -> UserRole:
        return self._role

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def is_admin(self) -> bool:
        return self._role == UserRole.ADMIN

    def is_regular(self) -> bool:
        return self._role == UserRole.REGULAR

    def can_make_query(self, cost: float) -> bool:
        """
        Проверяет, может ли пользователь сделать запрос.

        Условия:
        - Админ: всегда может (запросы бесплатны)
        - Обычный: только при положительном балансе и достаточных средствах

        Args:
            cost: Стоимость запроса

        Returns:
            bool: True если может делать запрос
        """
        if self.is_admin():
            return True

        return self._is_active and self._balance >= 0 and self._balance >= cost

    def deduct_balance(self, amount: float) -> None:
        if self.is_admin():
            return
        self._balance -= amount

    def add_balance(self, amount: float) -> None:
        self._balance += amount

    def get_query_history(self) -> List['Query']:
        """
        Получает историю запросов пользователя.

        Returns:
            List[Query]: Список запросов пользователя
        """
        #TODO реализовать через repository/service слой
        pass

    def deactivate(self) -> None:
        self._is_active = False

    def activate(self) -> None:
        self._is_active = True
