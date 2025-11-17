from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ValidationResult:
    """Результат валидации"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: Optional[List[str]] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Добавляет сообщение об ошибке"""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Добавляет предупреждение"""
        self.warnings.append(message)

    def has_errors(self) -> bool:
        """Проверяет наличие ошибок"""
        return len(self.errors) > 0

    def get_error_message(self) -> str:
        """Возвращает объединенное сообщение об ошибках"""
        return "; ".join(self.errors)
