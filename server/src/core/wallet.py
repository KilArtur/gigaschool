from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from core.user import User


class Wallet:
    """Кошелек пользователя для управления балансом"""

    def __init__(
        self,
        id: int,
        user_id: int,
        balance: float = 0.0,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self._id: int = id
        self._user_id: int = user_id
        self._balance: float = balance
        self._created_at: datetime = created_at or datetime.now()
        self._updated_at: datetime = updated_at or datetime.now()

    @property
    def id(self) -> int:
        return self._id

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def balance(self) -> float:
        return self._balance

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    def can_deduct(self, amount: float) -> bool:
        """
        Проверяет возможность списания указанной суммы.

        Args:
            amount: Сумма для списания

        Returns:
            bool: True если баланс достаточен
        """
        return self._balance >= 0 and self._balance >= amount

    def is_positive(self) -> bool:
        """Проверяет, что баланс не отрицательный"""
        return self._balance >= 0

    def deduct_balance(self, amount: float, user: 'User') -> None:
        """
        Списывает средства с кошелька.

        Правила:
        - Админам средства НЕ списываются
        - Баланс должен быть неотрицательным
        - Баланс должен быть достаточным для списания

        Args:
            amount: Сумма для списания
            user: Пользователь-владелец кошелька

        Raises:
            ValueError: Если недостаточно средств или баланс отрицательный
        """
        if user.is_admin():
            return

        if not self.is_positive():
            raise ValueError(
                f"Cannot deduct from negative balance. Current balance: {self._balance:.2f}"
            )

        if not self.can_deduct(amount):
            raise ValueError(
                f"Insufficient balance. Required: {amount:.2f}, Available: {self._balance:.2f}"
            )

        self._balance -= amount
        self._updated_at = datetime.now()

    def add_balance(self, amount: float) -> None:
        """
        Пополняет баланс кошелька.

        Args:
            amount: Сумма пополнения

        Raises:
            ValueError: Если сумма не положительная
        """
        if amount <= 0:
            raise ValueError(f"Top-up amount must be positive, got: {amount}")

        self._balance += amount
        self._updated_at = datetime.now()

    def transfer_to(self, target_wallet: 'Wallet', amount: float, admin_user: 'User') -> None:
        """
        Переводит средства в другой кошелек.
        Доступно только администраторам.

        Args:
            target_wallet: Кошелек-получатель
            amount: Сумма перевода
            admin_user: Администратор, выполняющий операцию

        Raises:
            PermissionError: Если вызывающий не является администратором
            ValueError: Если сумма не положительная или недостаточно средств
        """
        if not admin_user.is_admin():
            raise PermissionError("Only administrators can transfer balance")

        if amount <= 0:
            raise ValueError(f"Transfer amount must be positive, got: {amount}")

        self.deduct_balance(amount, admin_user)

        target_wallet.add_balance(amount)

    def admin_top_up(self, amount: float, admin_user: 'User') -> None:
        """
        Пополняет кошелек пользователя администратором.
        Средства создаются "из воздуха".

        Args:
            amount: Сумма пополнения
            admin_user: Администратор, выполняющий операцию

        Raises:
            PermissionError: Если вызывающий не является администратором
            ValueError: Если сумма не положительная
        """
        if not admin_user.is_admin():
            raise PermissionError("Only administrators can top up user balances")

        self.add_balance(amount)

    def can_afford(self, amount: float, user: 'User') -> bool:
        """
        Проверяет, может ли пользователь позволить себе операцию.

        Args:
            amount: Требуемая сумма
            user: Пользователь

        Returns:
            bool: True если может (админ всегда может, обычный - если баланс достаточен)
        """
        if user.is_admin():
            return True

        return self.is_positive() and self.can_deduct(amount)

    def refund(self, amount: float) -> None:
        """
        Возвращает средства на кошелек (например, при ошибке операции).

        Args:
            amount: Сумма возврата

        Raises:
            ValueError: Если сумма не положительная
        """
        if amount <= 0:
            raise ValueError(f"Refund amount must be positive, got: {amount}")

        self.add_balance(amount)