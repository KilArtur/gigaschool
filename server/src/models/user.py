from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from models.user_role import UserRole

if TYPE_CHECKING:
    from models.query import Query


class User:
    """Модель пользователя системы"""

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

    # Методы для проверки роли (полиморфизм)
    def is_admin(self) -> bool:
        """Проверяет, является ли пользователь администратором"""
        return self._role == UserRole.ADMIN

    def is_regular(self) -> bool:
        """Проверяет, является ли пользователь обычным пользователем"""
        return self._role == UserRole.REGULAR

    # Методы работы с балансом
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
        """
        Списывает средства с баланса.

        Правила:
        - Админам средства НЕ списываются
        - Списание происходит только если баланс достаточен

        Args:
            amount: Сумма для списания

        Raises:
            ValueError: Если недостаточно средств или баланс отрицательный
        """
        if self.is_admin():
            # Админы не платят, списание не происходит
            return

        if self._balance < 0:
            raise ValueError(
                f"Cannot deduct from negative balance. Current balance: {self._balance:.2f}"
            )

        if self._balance < amount:
            raise ValueError(
                f"Insufficient balance. Required: {amount:.2f}, Available: {self._balance:.2f}"
            )

        self._balance -= amount

    def add_balance(self, amount: float) -> None:
        """
        Пополняет баланс пользователя.

        Args:
            amount: Сумма пополнения

        Raises:
            ValueError: Если сумма не положительная
        """
        if amount <= 0:
            raise ValueError(f"Top-up amount must be positive, got: {amount}")

        self._balance += amount

    # Методы для администраторов
    def top_up_user_balance(self, target_user: 'User', amount: float) -> None:
        """
        Пополняет баланс другому пользователю по username.
        Доступно только администраторам.

        Args:
            target_user: Пользователь, которому пополняется баланс
            amount: Сумма пополнения

        Raises:
            PermissionError: Если вызывающий не является администратором
            ValueError: Если сумма не положительная
        """
        if not self.is_admin():
            raise PermissionError("Only administrators can top up user balances")

        if amount <= 0:
            raise ValueError(f"Top-up amount must be positive, got: {amount}")

        target_user.add_balance(amount)

    def get_query_history(self) -> List['Query']:
        """
        Получает историю запросов пользователя.

        Returns:
            List[Query]: Список запросов пользователя
        """
        # Будет реализовано через repository/service слой
        pass

    def deactivate(self) -> None:
        """Деактивирует аккаунт пользователя"""
        self._is_active = False

    def activate(self) -> None:
        """Активирует аккаунт пользователя"""
        self._is_active = True
