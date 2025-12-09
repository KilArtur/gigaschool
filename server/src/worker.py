import asyncio
import json
import aio_pika
from aio_pika import connect_robust
from sqlalchemy.orm import Session

from database.engine import SessionLocal
from database.repositories import QueryRepository, UserRepository, TransactionRepository, DocumentRepository
from core.services.LLMService import LLMService
from core.services.QdrantService import QdrantService
from core.services.RerankerService import RerankerService
from core.query import Query
from core.user import User
from core.document import Document
from core.models.query_status import QueryStatus
from core.models.transaction_type import TransactionType
from core.models.transaction_status import TransactionStatus
from config.Config import CONFIG
from utils.logger import get_logger

log = get_logger("Worker")

llm_service = None
qdrant_service = None
reranker_service = None

async def init_services():
    global llm_service, qdrant_service, reranker_service

    log.info("Инициализация сервисов...")
    llm_service = LLMService()
    qdrant_service = QdrantService()
    reranker_service = RerankerService()
    log.info("Все сервисы инициализированы")

async def process_query_task(message: aio_pika.IncomingMessage):
    async with message.process():
        db: Session = SessionLocal()
        try:
            body = json.loads(message.body.decode())
            query_id = body['query_id']
            log.info(f"Обработка query_id={query_id}")

            query_repo = QueryRepository(db)
            user_repo = UserRepository(db)
            transaction_repo = TransactionRepository(db)
            document_repo = DocumentRepository(db)

            query_model = query_repo.get_by_id(query_id)
            if not query_model:
                log.error(f"Query {query_id} не найден")
                return

            if query_model.status != QueryStatus.PENDING:
                log.warning(f"Query {query_id} уже обработан (status={query_model.status})")
                return

            query_model.status = QueryStatus.PROCESSING
            query_repo.update(query_model)
            db.commit()

            user_model = user_repo.get_by_id(query_model.user_id)
            document_model = document_repo.get_by_id(query_model.document_id)

            user = User(
                id=user_model.id,
                username=user_model.username,
                email=user_model.email,
                password_hash=user_model.password_hash,
                balance=user_model.balance,
                role=user_model.role,
                created_at=user_model.created_at,
                is_active=user_model.is_active
            )

            document = Document(
                id=document_model.id,
                user_id=document_model.user_id,
                filename=document_model.filename,
                file_path=document_model.file_path,
                upload_date=document_model.upload_date,
                status=document_model.status,
                chunk_count=document_model.chunk_count,
                page_count=document_model.page_count,
                file_size_mb=document_model.file_size_mb
            )

            query = Query(
                id=query_model.id,
                user_id=query_model.user_id,
                document_id=query_model.document_id,
                question=query_model.question
            )

            log.info(f"Query {query_id}: запуск RAG pipeline")
            answer = await query.execute(
                user=user,
                document=document,
                llm_service=llm_service,
                qdrant_service=qdrant_service,
                reranker_service=reranker_service
            )

            query_model.answer = answer
            query_model.status = QueryStatus.COMPLETED
            query_model.cost = query.cost
            query_model.input_tokens = query.input_tokens
            query_model.output_tokens = query.output_tokens
            query_model.total_tokens = query.total_tokens
            query_repo.update(query_model)

            user_repo.update_balance(user_model.id, user_model.balance - query.cost)

            if query.cost > 0:
                transaction_repo.create(
                    user_id=user_model.id,
                    amount=query.cost,
                    transaction_type=TransactionType.QUERY_CHARGE,
                    status=TransactionStatus.COMPLETED,
                    description=f"Query #{query_id}: {query_model.question[:50]}...",
                    related_query_id=query_id
                )

            db.commit()
            log.info(f"Query {query_id} успешно завершен. Cost: {query.cost}")

        except Exception as e:
            db.rollback()
            log.error(f"Ошибка обработки query {query_id}: {e}")

            try:
                query_model.status = QueryStatus.FAILED
                query_model.answer = f"Error: {str(e)}"
                query_repo.update(query_model)
                db.commit()
            except Exception as inner_e:
                log.error(f"Не удалось обновить статус query {query_id}: {inner_e}")

        finally:
            db.close()

async def main():
    await init_services()

    connection = await connect_robust(
        host=CONFIG.rabbitmq.host,
        port=CONFIG.rabbitmq.port,
        login=CONFIG.rabbitmq.user,
        password=CONFIG.rabbitmq.password,
    )

    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)

    queue = await channel.declare_queue(
        CONFIG.rabbitmq.queue_name,
        durable=True
    )

    log.info(f"Воркер запущен. Ожидание задач из очереди '{CONFIG.rabbitmq.queue_name}'...")

    await queue.consume(process_query_task)

    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
