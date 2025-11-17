from typing import TYPE_CHECKING

from services.abc.BaseValidator import BaseValidator
from models.validation_result import ValidationResult

if TYPE_CHECKING:
    from models.user import User


class BalanceValidator(BaseValidator):
    """Валидатор для проверки баланса пользователя перед выполнением операции"""

    def __init__(self, user: 'User', required_amount: float):
        """
        Args:
            user: Пользователь, баланс которого проверяется
            required_amount: Требуемая сумма для операции
        """
        self._user: 'User' = user
        self._required_amount: float = required_amount

    def validate(self) -> ValidationResult:
        """
        Выполняет валидацию баланса.

        Проверяет:
        - Активность аккаунта
        - Роль пользователя (админ проходит всегда)
        - Положительность баланса (не отрицательный)
        - Достаточность средств для операции

        Returns:
            ValidationResult: Результат валидации
        """
        result = ValidationResult(is_valid=True)

        # 1. Проверка активности аккаунта
        if not self._user.is_active:
            result.add_error("User account is not active")
            return result

        # 2. Админы проходят всегда (запросы бесплатны)
        if self._user.is_admin():
            return result

        # 3. Проверка на отрицательный баланс
        if not self._is_balance_positive():
            result.add_error(
                f"Negative balance detected. Current balance: {self._user.balance:.2f}. "
                f"Please top up your account."
            )
            return result

        # 4. Проверка достаточности средств
        if not self._has_sufficient_balance():
            result.add_error(
                f"Insufficient balance. Required: {self._required_amount:.2f}, "
                f"Available: {self._user.balance:.2f}. "
                f"Please top up your account."
            )

        return result

    def _is_balance_positive(self) -> bool:
        """Проверяет, что баланс не отрицательный"""
        return self._user.balance >= 0

    def _has_sufficient_balance(self) -> bool:
        """Проверяет достаточность баланса для операции"""
        return self._user.balance >= self._required_amount
