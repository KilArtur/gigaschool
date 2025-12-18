import json
import aio_pika
from aio_pika import connect_robust, Message

from config.Config import CONFIG
from utils.logger import get_logger

log = get_logger("RabbitMQService")

class RabbitMQService:
    def __init__(self):
        self.host = CONFIG.rabbitmq.host
        self.port = CONFIG.rabbitmq.port
        self.user = CONFIG.rabbitmq.user
        self.password = CONFIG.rabbitmq.password
        self.queue_name = CONFIG.rabbitmq.queue_name
        self.connection = None
        self.channel = None

    async def connect(self):
        if self.connection is None or self.connection.is_closed:
            self.connection = await connect_robust(
                host=self.host,
                port=self.port,
                login=self.user,
                password=self.password,
            )
            self.channel = await self.connection.channel()
            await self.channel.declare_queue(self.queue_name, durable=True)
            log.info(f"Подключение к RabbitMQ установлено: {self.host}:{self.port}")

    async def publish_query_task(self, query_id: int):
        await self.connect()

        message_body = json.dumps({"query_id": query_id})
        message = Message(
            body=message_body.encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )

        await self.channel.default_exchange.publish(
            message,
            routing_key=self.queue_name
        )

        log.info(f"Опубликована задача query_id={query_id} в очередь {self.queue_name}")

    async def close(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            log.info("Соединение с RabbitMQ закрыто")
