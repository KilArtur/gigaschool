from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from core.models.query_status import QueryStatus
from core.models.validation_result import ValidationResult
from core.services.validators.balance_validator import BalanceValidator
from core.services.LLMService import LLMService
from core.services.QdrantService import QdrantService
from core.services.RerankerService import RerankerService
from utils.prompt_loader import render_prompt

if TYPE_CHECKING:
    from core.user import User
    from core.document import Document


class Query:

    COST_PER_1000_TOKENS: float = 100.0  # рублей за 1000 токенов

    def __init__(
        self,
        id: int,
        user_id: int,
        document_id: int,
        question: str,
        answer: Optional[str] = None,
        cost: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        timestamp: Optional[datetime] = None,
        status: QueryStatus = QueryStatus.PENDING
    ):
        self._id: int = id
        self._user_id: int = user_id
        self._document_id: int = document_id
        self._question: str = question
        self._answer: Optional[str] = answer
        self._cost: float = cost
        self._input_tokens: int = input_tokens
        self._output_tokens: int = output_tokens
        self._total_tokens: int = total_tokens
        self._timestamp: datetime = timestamp or datetime.now()
        self._status: QueryStatus = status

    @property
    def id(self) -> int:
        return self._id

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def document_id(self) -> int:
        return self._document_id

    @property
    def question(self) -> str:
        return self._question

    @property
    def answer(self) -> Optional[str]:
        return self._answer

    @property
    def cost(self) -> float:
        return self._cost

    @property
    def input_tokens(self) -> int:
        return self._input_tokens

    @property
    def output_tokens(self) -> int:
        return self._output_tokens

    @property
    def total_tokens(self) -> int:
        return self._total_tokens

    @property
    def status(self) -> QueryStatus:
        return self._status

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    # Методы расчета стоимости
    @staticmethod
    def calculate_cost_from_tokens(total_tokens: int) -> float:
        """
        Рассчитывает стоимость по количеству токенов.

        Формула: (total_tokens / 1000) * 100 рублей

        Args:
            total_tokens: Общее количество токенов (input + output)

        Returns:
            float: Стоимость в рублях
        """
        cost = (total_tokens / 1000.0) * Query.COST_PER_1000_TOKENS
        return round(cost, 2)

    def calculate_cost(self, user: 'User') -> float:
        """
        Рассчитывает полную стоимость запроса на основе токенов.

        Использует:
        - self._input_tokens (из LLMService.total_input_token)
        - self._output_tokens (из LLMService.total_output_token)

        Args:
            user: Пользователь, выполняющий запрос

        Returns:
            float: Стоимость запроса в рублях (0 для админов)
        """
        if user.is_admin():
            return 0.0

        total = self._input_tokens + self._output_tokens
        self._total_tokens = total

        cost = self.calculate_cost_from_tokens(total)
        return cost

    async def execute(
        self,
        user: 'User',
        document: 'Document',
        llm_service: 'LLMService',
        qdrant_service: 'QdrantService',
        reranker_service: 'RerankerService'
    ) -> str:
        """
        Выполняет запрос к документу через RAG pipeline.

        Последовательность:
        1. Проверяет готовность документа
        2. Получает релевантные чанки (QdrantService)
        3. Переранжирует результаты (RerankerService)
        4. Формирует контекст
        5. Выполняет запрос к LLM
        6. Получает токены из LLMService
        7. Рассчитывает стоимость
        8. Валидирует баланс
        9. Списывает средства (только если баланс положительный)
        10. Сохраняет результат

        Args:
            user: Пользователь, выполняющий запрос
            document: Документ, к которому задается вопрос
            llm_service: Сервис для работы с LLM
            qdrant_service: Сервис для работы с векторной БД
            reranker_service: Сервис для переранжирования результатов

        Returns:
            str: Ответ на вопрос

        Raises:
            ValueError: Если документ не готов или баланс недостаточен
            Exception: При ошибке выполнения запроса
        """
        if not document.is_ready_for_queries():
            raise ValueError(
                f"Document {document.id} is not ready for queries. Status: {document.status.value}"
            )

        try:
            self._status = QueryStatus.PROCESSING

            search_results = qdrant_service.search_similar(self._question)

            if not search_results:
                raise ValueError("No relevant chunks found in the document")

            documents_for_rerank = [result['text'] for result in search_results]

            reranked_results = reranker_service.rerank(
                query=self._question,
                documents=documents_for_rerank
            )

            context = self._build_context(reranked_results)

            prompt = render_prompt("rag_answer_prompt").format(
                data=context,
                question=self._question
            )

            llm_service.total_input_token = 0
            llm_service.total_output_token = 0

            answer = await llm_service.fetch_completion(prompt)

            self._input_tokens = llm_service.total_input_token
            self._output_tokens = llm_service.total_output_token
            self._total_tokens = self._input_tokens + self._output_tokens

            cost = self.calculate_cost(user)
            self._cost = cost

            balance_validator = BalanceValidator(user, cost)
            validation_result: ValidationResult = balance_validator.validate()

            if not validation_result.is_valid:
                self._status = QueryStatus.FAILED
                raise ValueError(
                    f"Cannot complete query: {validation_result.get_error_message()}"
                )

            user.deduct_balance(cost)

            self._answer = answer
            self._status = QueryStatus.COMPLETED

            return answer

        except ValueError as e:
            self._status = QueryStatus.FAILED
            raise

        except Exception as e:
            self._status = QueryStatus.FAILED
            if hasattr(self, '_cost') and self._cost > 0:
                user.add_balance(self._cost)
            raise Exception(f"Query execution failed: {str(e)}")

    def _build_context(self, reranked_results: List[tuple]) -> str:
        """
        Формирует контекст из переранжированных результатов.

        Args:
            reranked_results: Список кортежей (index, text, score)

        Returns:
            str: Объединенный контекст
        """
        context_parts = []
        for idx, (original_idx, text, score) in enumerate(reranked_results, 1):
            context_parts.append(f"[Chunk {idx}]\n{text}\n")

        return "\n".join(context_parts)

    def mark_as_failed(self, error_message: str = "") -> None:
        self._status = QueryStatus.FAILED
        if error_message:
            self._answer = f"Error: {error_message}"
