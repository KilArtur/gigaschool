from abc import ABC, abstractmethod
from core.models.validation_result import ValidationResult


class BaseValidator(ABC):

    @abstractmethod
    def validate(self) -> ValidationResult:
        pass
