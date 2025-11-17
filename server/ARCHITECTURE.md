# Архитектура RAG Сервиса

## Обзор

Объектно-ориентированная архитектура RAG (Retrieval-Augmented Generation) сервиса для работы с PDF документами, реализующая:
- ✅ Инкапсуляцию через приватные поля и геттеры
- ✅ Наследование через абстрактные классы (BaseValidator)
- ✅ Полиморфизм через методы is_admin() и различное поведение для ролей

## Структура проекта

```
server/src/
├── models/                              # Модели данных
│   ├── __init__.py
│   ├── user_role.py                     # Enum: REGULAR, ADMIN
│   ├── document_status.py               # Enum: UPLOADED, PROCESSING, READY, FAILED
│   ├── query_status.py                  # Enum: PENDING, PROCESSING, COMPLETED, FAILED
│   ├── transaction_type.py              # Enum: TOP_UP, QUERY_CHARGE, REFUND, ADMIN_TOP_UP
│   ├── transaction_status.py            # Enum: PENDING, COMPLETED, REJECTED
│   ├── validation_result.py             # Dataclass для результатов валидации
│   ├── user.py                          # Модель пользователя
│   ├── document.py                      # Модель документа
│   ├── query.py                         # Модель запроса (интеграция с RAG)
│   └── transaction.py                   # Модель транзакции
│
├── services/
│   ├── abc/                             # Абстрактные классы
│   │   ├── __init__.py
│   │   ├── BaseValidator.py             # Базовый валидатор (наследование)
│   │   └── BaseUser.py                  # (существующий, не используется)
│   │
│   ├── validators/                      # Конкретные валидаторы
│   │   ├── __init__.py
│   │   ├── document_validator.py        # Валидация PDF документов
│   │   └── balance_validator.py         # Валидация баланса пользователя
│   │
│   ├── LLMService.py                    # Сервис работы с LLM (существующий)
│   ├── QdrantService.py                 # Сервис векторной БД (существующий)
│   ├── RerankerService.py               # Сервис переранжирования (существующий)
│   └── СhunksService.py                 # Сервис обработки чанков (существующий)
│
└── example_usage.py                     # Пример использования архитектуры
```

## Описание компонентов

### 1. Модели (Models)

#### User (models/user.py)
Базовая модель пользователя с поддержкой ролей.

**Поля:**
- `_id: int` - ID пользователя
- `_username: str` - Имя пользователя
- `_email: str` - Email
- `_password_hash: str` - Хэш пароля
- `_balance: float` - Баланс в рублях
- `_role: UserRole` - Роль (REGULAR или ADMIN)
- `_created_at: datetime` - Дата создания
- `_is_active: bool` - Активность аккаунта

**Ключевые методы:**
- `is_admin() -> bool` - Проверка роли администратора (полиморфизм)
- `is_regular() -> bool` - Проверка обычного пользователя
- `can_make_query(cost: float) -> bool` - Может ли делать запрос
- `deduct_balance(amount: float)` - Списание средств (НЕ списывает у админов)
- `add_balance(amount: float)` - Пополнение баланса
- `top_up_user_balance(target_user, amount)` - Пополнение другому пользователю (только админ)

**Реализация ООП принципов:**
- ✅ Инкапсуляция: приватные поля `_field`, доступ через `@property`
- ✅ Наследование: может наследоваться для специфических типов
- ✅ Полиморфизм: разное поведение для админов и обычных пользователей

#### Document (models/document.py)
Модель PDF документа для RAG.

**Поля:**
- `_id: int` - ID документа
- `_user_id: int` - ID владельца
- `_filename: str` - Имя файла
- `_file_path: str` - Путь к файлу
- `_status: DocumentStatus` - Статус обработки
- `_chunk_count: int` - Количество чанков
- `_page_count: int` - Количество страниц

**Ключевые методы:**
- `validate() -> ValidationResult` - Валидация документа
- `is_ready_for_queries() -> bool` - Готовность для запросов
- `process_for_rag(chunk_processor, qdrant_service)` - Обработка для RAG
- `mark_as_processing()`, `mark_as_ready()`, `mark_as_failed()` - Управление статусом

**Интеграция:**
- Использует `ChunkProcessor` для разбиения на чанки
- Использует `QdrantService` для загрузки embeddings

#### Query (models/query.py)
Модель запроса к документу (без сохранения контекста между запросами).

**Поля:**
- `_id: int` - ID запроса
- `_user_id: int` - ID пользователя
- `_document_id: int` - ID документа
- `_question: str` - Вопрос пользователя
- `_answer: str` - Ответ от LLM
- `_cost: float` - Стоимость запроса
- `_input_tokens: int` - Входные токены
- `_output_tokens: int` - Выходные токены
- `_total_tokens: int` - Всего токенов
- `_status: QueryStatus` - Статус запроса

**Ключевые методы:**
- `calculate_cost(user) -> float` - Расчет стоимости (100₽ за 1000 токенов)
- `execute(user, document, llm, qdrant, reranker) -> str` - Выполнение RAG запроса

**Логика execute():**
1. Проверяет готовность документа
2. Ищет релевантные чанки через `QdrantService.search_similar()`
3. Переранжирует через `RerankerService.rerank()`
4. Формирует контекст и промпт
5. Отправляет в `LLMService.fetch_completion()`
6. Получает токены: `llm_service.total_input_token`, `llm_service.total_output_token`
7. Рассчитывает стоимость
8. Проверяет баланс через `BalanceValidator`
9. Списывает средства (если баланс положительный)
10. Возвращает ответ

**Обработка ошибок:**
- При ошибке LLM - возврат списанных средств
- При недостаточном балансе - запрос не выполняется

#### Transaction (models/transaction.py)
Модель финансовой транзакции.

**Поля:**
- `_id: int` - ID транзакции
- `_user_id: int` - ID пользователя
- `_amount: float` - Сумма
- `_type: TransactionType` - Тип транзакции
- `_status: TransactionStatus` - Статус
- `_related_query_id: int` - Связанный запрос
- `_processed_by_admin_id: int` - ID админа (для пополнений)

**Ключевые методы:**
- `process()` - Завершить транзакцию
- `reject(reason)` - Отклонить транзакцию

### 2. Валидаторы (Validators)

#### BaseValidator (services/abc/BaseValidator.py)
Абстрактный базовый класс для всех валидаторов.

```python
class BaseValidator(ABC):
    @abstractmethod
    def validate(self) -> ValidationResult:
        pass
```

**Реализация ООП:**
- ✅ Наследование: базовый класс для всех валидаторов
- ✅ Полиморфизм: каждый валидатор реализует свою логику

#### DocumentValidator (services/validators/document_validator.py)
Валидатор PDF документов.

**Проверки:**
- ✅ Существование файла
- ✅ Формат PDF (расширение + magic bytes `%PDF`)
- ✅ Размер файла (макс. 10 МБ)
- ✅ Читаемость PDF (не поврежден, не зашифрован)
- ✅ Количество страниц (макс. 500)

**Использует:** `PyMuPDF (fitz)`

#### BalanceValidator (services/validators/balance_validator.py)
Валидатор баланса пользователя.

**Проверки:**
- ✅ Активность аккаунта
- ✅ Роль (админы проходят всегда)
- ✅ Положительность баланса (не отрицательный)
- ✅ Достаточность средств

### 3. ValidationResult (models/validation_result.py)
Dataclass для результатов валидации.

**Поля:**
- `is_valid: bool` - Результат валидации
- `errors: List[str]` - Список ошибок
- `warnings: List[str]` - Список предупреждений

**Методы:**
- `add_error(message)` - Добавить ошибку
- `add_warning(message)` - Добавить предупреждение
- `get_error_message()` - Получить объединенное сообщение

## Тарификация

### Формула расчета стоимости:
```
cost = (input_tokens + output_tokens) / 1000 × 100₽
```

### Особенности:
- Админы платят 0₽ (запросы бесплатны)
- Обычные пользователи платят по факту использования токенов
- Токены считаются автоматически через `LLMService.total_input_token` и `total_output_token`
- При отрицательном балансе запросы блокируются
- При ошибке LLM средства возвращаются

## Принципы ООП

### 1. Инкапсуляция
```python
class User:
    def __init__(self, id: int, balance: float):
        self._id: int = id          # Приватное поле
        self._balance: float = balance

    @property
    def balance(self) -> float:     # Геттер
        return self._balance
```

### 2. Наследование
```python
class BaseValidator(ABC):           # Абстрактный класс
    @abstractmethod
    def validate(self) -> ValidationResult:
        pass

class DocumentValidator(BaseValidator):  # Наследование
    def validate(self) -> ValidationResult:
        # Реализация
```

### 3. Полиморфизм
```python
# В User
def deduct_balance(self, amount: float):
    if self.is_admin():
        return  # Админы не платят
    self._balance -= amount  # Обычные платят

# В Query
def calculate_cost(self, user: User) -> float:
    if user.is_admin():
        return 0.0  # Админы - бесплатно
    return (self._total_tokens / 1000.0) * 100.0
```

## Использование

### Пример 1: Создание пользователя
```python
from models import User, UserRole

# Обычный пользователь
user = User(
    id=1,
    username="ivan",
    email="ivan@example.com",
    password_hash="hash",
    balance=1000.0,
    role=UserRole.REGULAR
)

# Админ
admin = User(
    id=2,
    username="admin",
    email="admin@example.com",
    password_hash="hash",
    balance=0.0,
    role=UserRole.ADMIN
)
```

### Пример 2: Обработка документа
```python
from models import Document, DocumentStatus
from services.СhunksService import ChunkProcessor
from services.QdrantService import QdrantService

document = Document(
    id=1,
    user_id=user.id,
    filename="guide.pdf",
    file_path="/path/to/guide.pdf",
    status=DocumentStatus.UPLOADED
)

# Валидация
result = document.validate()
if not result.is_valid:
    print(f"Ошибки: {result.get_error_message()}")

# Обработка
chunk_processor = ChunkProcessor()
qdrant_service = QdrantService()
document.process_for_rag(chunk_processor, qdrant_service)
```

### Пример 3: Выполнение запроса
```python
from models import Query
from services.LLMService import LLMService
from services.RerankerService import RerankerService

query = Query(
    id=1,
    user_id=user.id,
    document_id=document.id,
    question="Что такое машинное обучение?"
)

llm_service = LLMService()
reranker_service = RerankerService()

answer = await query.execute(
    user=user,
    document=document,
    llm_service=llm_service,
    qdrant_service=qdrant_service,
    reranker_service=reranker_service
)

print(f"Ответ: {answer}")
print(f"Стоимость: {query.cost:.2f} руб.")
print(f"Токенов: {query.total_tokens}")
```

### Пример 4: Пополнение баланса админом
```python
# Админ пополняет баланс пользователю
admin.top_up_user_balance(user, 500.0)
print(f"Новый баланс: {user.balance:.2f} руб.")

# Создание транзакции
transaction = Transaction(
    id=1,
    user_id=user.id,
    amount=500.0,
    transaction_type=TransactionType.ADMIN_TOP_UP,
    status=TransactionStatus.COMPLETED,
    processed_by_admin_id=admin.id
)
```

## Запуск примера

```bash
cd server/src
python example_usage.py
```

Пример демонстрирует:
1. Создание пользователей разных ролей
2. Загрузку и обработку документа
3. Выполнение запросов с проверкой баланса
4. Различия между обычным пользователем и админом
5. Пополнение баланса администратором

## Интеграция с существующими сервисами

### LLMService
- **Используется:** `fetch_completion(prompt)` для получения ответов
- **Токены:** `total_input_token`, `total_output_token` для тарификации

### QdrantService
- **Используется:** `search_similar(query)` для поиска релевантных чанков
- **Используется:** `add_chunks_directly(chunks)` для загрузки документа

### RerankerService
- **Используется:** `rerank(query, documents)` для улучшения результатов

### ChunkProcessor
- **Используется:** `process_pdf(file_path, title)` для разбиения PDF на чанки

## Следующие шаги

1. **База данных:** Добавить ORM (SQLAlchemy) для персистентности
2. **API:** Создать REST API endpoints для моделей
3. **Аутентификация:** Добавить JWT токены для авторизации
4. **Frontend:** Веб-интерфейс для пользователей
5. **Тесты:** Unit и integration тесты для всех компонентов

## Лицензия

Проект для учебных целей.
