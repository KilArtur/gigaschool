"""
Пример использования объектной модели RAG сервиса

Демонстрирует:
1. Создание пользователей (обычный и админ)
2. Загрузку и обработку документа
3. Выполнение запросов с проверкой баланса
4. Различия между обычным пользователем и администратором
"""

import asyncio
from models import (
    User, Document, Query, Transaction,
    UserRole, DocumentStatus, QueryStatus,
    TransactionType, TransactionStatus
)
from services.LLMService import LLMService
from services.QdrantService import QdrantService
from services.RerankerService import RerankerService
from services.СhunksService import ChunkProcessor


async def main():
    print("=" * 80)
    print("RAG Сервис - Пример использования объектной модели")
    print("=" * 80)

    # ============================================================================
    # 1. Создание пользователей
    # ============================================================================
    print("\n1. Создание пользователей:")
    print("-" * 80)

    # Обычный пользователь
    regular_user = User(
        id=1,
        username="ivan_petrov",
        email="ivan@example.com",
        password_hash="hashed_password_123",
        balance=1000.0,  # 1000 рублей на балансе
        role=UserRole.REGULAR
    )
    print(f"✓ Создан обычный пользователь: {regular_user.username}")
    print(f"  - Баланс: {regular_user.balance:.2f} руб.")
    print(f"  - Роль: {regular_user.role.value}")
    print(f"  - Админ: {regular_user.is_admin()}")

    # Администратор
    admin_user = User(
        id=2,
        username="admin",
        email="admin@example.com",
        password_hash="admin_hashed_password",
        balance=0.0,  # Админу баланс не нужен
        role=UserRole.ADMIN
    )
    print(f"\n✓ Создан администратор: {admin_user.username}")
    print(f"  - Баланс: {admin_user.balance:.2f} руб.")
    print(f"  - Роль: {admin_user.role.value}")
    print(f"  - Админ: {admin_user.is_admin()}")

    # ============================================================================
    # 2. Загрузка и обработка документа
    # ============================================================================
    print("\n\n2. Загрузка и обработка документа:")
    print("-" * 80)

    document = Document(
        id=1,
        user_id=regular_user.id,
        filename="machine_learning_guide.pdf",
        file_path="/path/to/documents/ml_guide.pdf",
        status=DocumentStatus.UPLOADED
    )
    print(f"✓ Создан документ: {document.filename}")
    print(f"  - Статус: {document.status.value}")
    print(f"  - Пользователь: {regular_user.username}")

    # Валидация документа
    print("\n  Валидация документа...")
    validation_result = document.validate()
    if validation_result.is_valid:
        print("  ✓ Документ прошел валидацию")
    else:
        print(f"  ✗ Ошибки валидации: {validation_result.get_error_message()}")
        return

    # Обработка документа для RAG
    print("\n  Обработка документа для RAG...")
    chunk_processor = ChunkProcessor()
    qdrant_service = QdrantService()

    try:
        document.process_for_rag(chunk_processor, qdrant_service)
        print(f"  ✓ Документ обработан")
        print(f"    - Статус: {document.status.value}")
        print(f"    - Чанков: {document.chunk_count}")
        print(f"    - Страниц: {document.page_count}")
    except Exception as e:
        print(f"  ✗ Ошибка обработки: {e}")
        return

    # ============================================================================
    # 3. Запросы обычного пользователя
    # ============================================================================
    print("\n\n3. Запросы обычного пользователя:")
    print("-" * 80)

    print(f"Баланс до запроса: {regular_user.balance:.2f} руб.")

    # Создаем запрос
    query1 = Query(
        id=1,
        user_id=regular_user.id,
        document_id=document.id,
        question="Что такое машинное обучение?"
    )

    print(f"\nВопрос: {query1.question}")
    print("Выполнение запроса...")

    # Инициализируем сервисы
    llm_service = LLMService()
    reranker_service = RerankerService()

    try:
        answer = await query1.execute(
            user=regular_user,
            document=document,
            llm_service=llm_service,
            qdrant_service=qdrant_service,
            reranker_service=reranker_service
        )

        print(f"\n✓ Запрос выполнен успешно!")
        print(f"  - Статус: {query1.status.value}")
        print(f"  - Входных токенов: {query1.input_tokens}")
        print(f"  - Выходных токенов: {query1.output_tokens}")
        print(f"  - Всего токенов: {query1.total_tokens}")
        print(f"  - Стоимость: {query1.cost:.2f} руб.")
        print(f"  - Ответ: {answer[:100]}...")

        print(f"\nБаланс после запроса: {regular_user.balance:.2f} руб.")
        print(f"Списано: {query1.cost:.2f} руб.")

        # Создаем транзакцию для истории
        transaction = Transaction(
            id=1,
            user_id=regular_user.id,
            amount=-query1.cost,
            transaction_type=TransactionType.QUERY_CHARGE,
            status=TransactionStatus.COMPLETED,
            related_query_id=query1.id,
            description=f"Запрос к документу: {document.filename}"
        )
        print(f"\n✓ Транзакция создана: {transaction.type.value}")

    except ValueError as e:
        print(f"\n✗ Ошибка выполнения: {e}")
    except Exception as e:
        print(f"\n✗ Неожиданная ошибка: {e}")

    # ============================================================================
    # 4. Попытка запроса с недостаточным балансом
    # ============================================================================
    print("\n\n4. Попытка запроса с недостаточным балансом:")
    print("-" * 80)

    # Создаем пользователя с нулевым балансом
    poor_user = User(
        id=3,
        username="poor_user",
        email="poor@example.com",
        password_hash="password",
        balance=0.0,
        role=UserRole.REGULAR
    )

    print(f"Пользователь: {poor_user.username}")
    print(f"Баланс: {poor_user.balance:.2f} руб.")

    query2 = Query(
        id=2,
        user_id=poor_user.id,
        document_id=document.id,
        question="Какие алгоритмы машинного обучения существуют?"
    )

    print(f"\nВопрос: {query2.question}")
    print("Попытка выполнения запроса...")

    try:
        answer = await query2.execute(
            user=poor_user,
            document=document,
            llm_service=llm_service,
            qdrant_service=qdrant_service,
            reranker_service=reranker_service
        )
    except ValueError as e:
        print(f"\n✗ Запрос отклонен: {e}")
        print(f"  - Статус запроса: {query2.status.value}")
        print(f"  - Баланс остался: {poor_user.balance:.2f} руб.")

    # ============================================================================
    # 5. Запрос администратора (бесплатно)
    # ============================================================================
    print("\n\n5. Запрос администратора (бесплатно):")
    print("-" * 80)

    print(f"Администратор: {admin_user.username}")
    print(f"Баланс до запроса: {admin_user.balance:.2f} руб.")

    query3 = Query(
        id=3,
        user_id=admin_user.id,
        document_id=document.id,
        question="Расскажи о нейронных сетях"
    )

    print(f"\nВопрос: {query3.question}")
    print("Выполнение запроса...")

    try:
        answer = await query3.execute(
            user=admin_user,
            document=document,
            llm_service=llm_service,
            qdrant_service=qdrant_service,
            reranker_service=reranker_service
        )

        print(f"\n✓ Запрос администратора выполнен!")
        print(f"  - Статус: {query3.status.value}")
        print(f"  - Всего токенов: {query3.total_tokens}")
        print(f"  - Стоимость: {query3.cost:.2f} руб. (бесплатно для админа)")
        print(f"  - Ответ: {answer[:100]}...")

        print(f"\nБаланс после запроса: {admin_user.balance:.2f} руб.")
        print("✓ Средства не списаны (админ)")

    except Exception as e:
        print(f"\n✗ Ошибка: {e}")

    # ============================================================================
    # 6. Пополнение баланса администратором
    # ============================================================================
    print("\n\n6. Пополнение баланса администратором:")
    print("-" * 80)

    print(f"Баланс пользователя {poor_user.username} до пополнения: {poor_user.balance:.2f} руб.")

    try:
        admin_user.top_up_user_balance(poor_user, 500.0)
        print(f"\n✓ Баланс пополнен администратором {admin_user.username}")
        print(f"  - Сумма пополнения: 500.00 руб.")
        print(f"  - Новый баланс: {poor_user.balance:.2f} руб.")

        # Создаем транзакцию пополнения
        top_up_transaction = Transaction(
            id=2,
            user_id=poor_user.id,
            amount=500.0,
            transaction_type=TransactionType.ADMIN_TOP_UP,
            status=TransactionStatus.COMPLETED,
            processed_by_admin_id=admin_user.id,
            description=f"Пополнение администратором {admin_user.username}"
        )
        print(f"✓ Транзакция пополнения создана")

    except PermissionError as e:
        print(f"\n✗ Ошибка доступа: {e}")

    print("\n" + "=" * 80)
    print("Пример завершен")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
