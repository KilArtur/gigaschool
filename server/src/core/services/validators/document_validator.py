import os
from typing import List
import fitz  # PyMuPDF

from core.services.abc.BaseValidator import BaseValidator
from core.models.validation_result import ValidationResult


class DocumentValidator(BaseValidator):
    """Валидатор для проверки загружаемых PDF документов"""

    # Константы валидации
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = ['.pdf']
    MAX_PAGE_COUNT: int = 500

    def __init__(self, file_path: str, max_size_mb: int = MAX_FILE_SIZE_MB):
        """
        Args:
            file_path: Путь к файлу для валидации
            max_size_mb: Максимальный размер файла в МБ
        """
        self._file_path: str = file_path
        self._max_size_mb: int = max_size_mb

    def validate(self) -> ValidationResult:
        """
        Выполняет полную валидацию документа.

        Проверяет:
        - Существование файла
        - Формат файла (только PDF)
        - Размер файла
        - Читаемость PDF (не поврежден, не зашифрован)
        - Количество страниц

        Returns:
            ValidationResult: Результат валидации
        """
        result = ValidationResult(is_valid=True)

        # 1. Проверка существования
        if not self._file_exists():
            result.add_error(f"File not found: {self._file_path}")
            return result

        # 2. Проверка формата
        if not self._is_pdf():
            result.add_error(f"Invalid file format. Only PDF files are allowed.")
            return result

        # 3. Проверка размера
        if not self._check_file_size():
            file_size_mb = self._get_file_size_mb()
            result.add_error(
                f"File size {file_size_mb:.2f}MB exceeds maximum allowed size {self._max_size_mb}MB"
            )

        # 4. Проверка читаемости
        is_readable, error_msg = self._is_readable()
        if not is_readable:
            result.add_error(error_msg)
            return result

        # 5. Проверка количества страниц
        page_count = self._get_page_count()
        if page_count > self.MAX_PAGE_COUNT:
            result.add_error(
                f"Document has {page_count} pages, maximum allowed is {self.MAX_PAGE_COUNT}"
            )

        return result

    def _file_exists(self) -> bool:
        """Проверяет существование файла"""
        return os.path.exists(self._file_path) and os.path.isfile(self._file_path)

    def _is_pdf(self) -> bool:
        """Проверяет, является ли файл PDF по расширению и magic bytes"""
        # Проверка расширения
        _, ext = os.path.splitext(self._file_path)
        if ext.lower() not in self.ALLOWED_EXTENSIONS:
            return False

        # Проверка magic bytes (PDF начинается с %PDF)
        try:
            with open(self._file_path, 'rb') as f:
                header = f.read(4)
                return header == b'%PDF'
        except Exception:
            return False

    def _check_file_size(self) -> bool:
        """Проверяет размер файла"""
        file_size_mb = self._get_file_size_mb()
        return file_size_mb <= self._max_size_mb

    def _get_file_size_mb(self) -> float:
        """Возвращает размер файла в МБ"""
        file_size_bytes = os.path.getsize(self._file_path)
        return file_size_bytes / (1024 * 1024)

    def _is_readable(self) -> tuple[bool, str]:
        """
        Проверяет, читаем ли PDF (не поврежден, не зашифрован)

        Returns:
            tuple[bool, str]: (is_readable, error_message)
        """
        try:
            doc = fitz.open(self._file_path)

            # Проверка на шифрование
            if doc.is_encrypted:
                doc.close()
                return False, "PDF file is encrypted or password protected"

            # Попытка прочитать первую страницу
            if len(doc) > 0:
                _ = doc[0].get_text()

            doc.close()
            return True, ""

        except Exception as e:
            return False, f"PDF file is corrupted or cannot be read: {str(e)}"

    def _get_page_count(self) -> int:
        """Возвращает количество страниц в PDF"""
        try:
            doc = fitz.open(self._file_path)
            page_count = len(doc)
            doc.close()
            return page_count
        except Exception:
            return 0
