from enum import Enum


class TransactionType(Enum):
    """Типы транзакций"""
    TOP_UP = "top_up"              # Пополнение пользователем
    QUERY_CHARGE = "query_charge"  # Списание за запрос
    REFUND = "refund"              # Возврат средств
    ADMIN_TOP_UP = "admin_top_up"  # Пополнение админом
