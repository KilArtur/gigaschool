from abc import ABC, abstractmethod
from core.models.validation_result import ValidationResult


class BaseValidator(ABC):
    """1AB@0:B=K9 107>2K9 :;0AA 4;O 2A5E 20;840B>@>2"""

    @abstractmethod
    def validate(self) -> ValidationResult:
        """
        K?>;=O5B 20;840F8N 8 2>72@0I05B @57C;LB0B.

        Returns:
            ValidationResult:  57C;LB0B 20;840F88 A D;03>< is_valid 8 A?8A:>< >H81>:
        """
        pass
