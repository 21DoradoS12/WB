import asyncio
import json
import logging
from typing import Callable

from aio_pika import connect_robust, IncomingMessage

from src.core.config.settings import settings

log = logging.getLogger(__name__)


class QueueConsumer:
    def __init__(self, queue_name: str, handler_func: Callable):
        self.queue_name = queue_name
        self.handler_func = handler_func
        self.rabbitmq_url = settings.rabbitmq_url

    async def start(self):
        connection = await connect_robust(self.rabbitmq_url)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        # Объявляем очередь (если не существует)
        queue = await channel.declare_queue(
            self.queue_name,
            durable=True,
        )

        log.info(f"👂 Ожидание сообщений в очереди '{self.queue_name}'...")
        await queue.consume(self._on_message)

        while True:
            await asyncio.sleep(1)

    async def _on_message(self, message: IncomingMessage):
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                log.info(f"Получено сообщение: {data}")

                await self.handler_func(data)
                log.info("Сообщение обработано успешно.")
            except Exception as e:
                log.error(
                    f"[ERROR] Ошибка обработки сообщения {message.body.decode()} из '{self.queue_name}': {e}",
                    exc_info=True,
                )
