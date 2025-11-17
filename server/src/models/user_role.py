from enum import Enum


class UserRole(Enum):
    """Роли пользователей в системе"""
    REGULAR = "regular"
    ADMIN = "admin"
