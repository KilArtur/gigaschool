from datetime import datetime
from typing import Optional, TYPE_CHECKING

from models.document_status import DocumentStatus
from models.validation_result import ValidationResult
from services.validators.document_validator import DocumentValidator

if TYPE_CHECKING:
    from services.СhunksService import ChunkProcessor
    from services.QdrantService import QdrantService


class Document:
    """Загруженный PDF документ для RAG"""

    def __init__(
        self,
        id: int,
        user_id: int,
        filename: str,
        file_path: str,
        upload_date: Optional[datetime] = None,
        status: DocumentStatus = DocumentStatus.UPLOADED,
        chunk_count: int = 0,
        page_count: int = 0,
        file_size_mb: float = 0.0
    ):
        self._id: int = id
        self._user_id: int = user_id
        self._filename: str = filename
        self._file_path: str = file_path
        self._upload_date: datetime = upload_date or datetime.now()
        self._status: DocumentStatus = status
        self._chunk_count: int = chunk_count
        self._page_count: int = page_count
        self._file_size_mb: float = file_size_mb

    # Геттеры
    @property
    def id(self) -> int:
        return self._id

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def file_path(self) -> str:
        return self._file_path

    @property
    def status(self) -> DocumentStatus:
        return self._status

    @property
    def chunk_count(self) -> int:
        return self._chunk_count

    @property
    def page_count(self) -> int:
        return self._page_count

    @property
    def upload_date(self) -> datetime:
        return self._upload_date

    @property
    def file_size_mb(self) -> float:
        return self._file_size_mb

    # Методы валидации и обработки
    def validate(self) -> ValidationResult:
        """
        Валидирует документ перед обработкой.

        Returns:
            ValidationResult: Результат валидации
        """
        validator = DocumentValidator(self._file_path)
        return validator.validate()

    def is_ready_for_queries(self) -> bool:
        """
        Проверяет, готов ли документ для запросов.

        Returns:
            bool: True если документ обработан и готов
        """
        return self._status == DocumentStatus.READY

    def mark_as_processing(self) -> None:
        """Помечает документ как обрабатываемый"""
        self._status = DocumentStatus.PROCESSING

    def mark_as_ready(self, chunk_count: int, page_count: int) -> None:
        """
        Помечает документ как готовый к использованию.

        Args:
            chunk_count: Количество чанков после обработки
            page_count: Количество страниц в документе
        """
        self._status = DocumentStatus.READY
        self._chunk_count = chunk_count
        self._page_count = page_count

    def mark_as_failed(self) -> None:
        """Помечает документ как проваленный при обработке"""
        self._status = DocumentStatus.FAILED

    def process_for_rag(
        self,
        chunk_processor: 'ChunkProcessor',
        qdrant_service: 'QdrantService'
    ) -> None:
        """
        Обрабатывает документ для RAG:
        1. Валидирует PDF
        2. Извлекает текст и разбивает на чанки
        3. Загружает чанки в Qdrant с embeddings

        Args:
            chunk_processor: Сервис для обработки чанков
            qdrant_service: Сервис для работы с векторной БД

        Raises:
            ValueError: Если валидация не прошла
            Exception: При ошибке обработки
        """
        # 1. Валидация
        validation_result = self.validate()
        if not validation_result.is_valid:
            self.mark_as_failed()
            raise ValueError(
                f"Document validation failed: {validation_result.get_error_message()}"
            )

        try:
            self.mark_as_processing()

            # 2. Обработка PDF и создание чанков
            chunks = chunk_processor.process_pdf(self._file_path, title=self._filename)

            if not chunks:
                self.mark_as_failed()
                raise ValueError("Failed to process PDF: no chunks created")

            # 3. Загрузка чанков в Qdrant (embeddings создаются внутри add_chunks_directly)
            uploaded_count = qdrant_service.add_chunks_directly(chunks)

            # 4. Получаем количество страниц
            import fitz
            doc = fitz.open(self._file_path)
            page_count = len(doc)
            doc.close()

            # 5. Обновляем статус
            self.mark_as_ready(chunk_count=uploaded_count, page_count=page_count)

        except Exception as e:
            self.mark_as_failed()
            raise Exception(f"Document processing failed: {str(e)}")
