import asyncio
import json
import logging

from aio_pika import connect_robust, Message, DeliveryMode
from aiormq import AMQPConnectionError

from src.core.config.settings import settings

log = logging.getLogger(__name__)


async def send_to_queue(
    queue_name: str, data: dict, retry: int = 3, delay: float = 2.0
):
    """
    Отправляет данные в очередь RabbitMQ с retry и reconnect.

    :param queue_name: имя очереди
    :param data: dict с данными
    :param retry: количество попыток переподключения
    :param delay: задержка между попытками (сек)
    """
    attempt = 0
    while attempt < retry:
        try:
            connection = await connect_robust(settings.rabbitmq_url)
            channel = await connection.channel()

            await channel.declare_queue(queue_name, durable=True)

            message = Message(
                body=json.dumps(data).encode(), delivery_mode=DeliveryMode.PERSISTENT
            )

            await channel.default_exchange.publish(message, routing_key=queue_name)

            log.info(f"✅ Сообщение отправлено в очередь '{queue_name}': {data}")
            await connection.close()
            return True

        except AMQPConnectionError as e:
            attempt += 1
            log.warning(
                f"⚠ Ошибка подключения к RabbitMQ: {e}. Попытка {attempt}/{retry}"
            )
            await asyncio.sleep(delay)

        except Exception as e:
            log.error(f"❌ Ошибка отправки сообщения в очередь '{queue_name}': {e}")
            return False

    log.error(
        f"❌ Не удалось отправить сообщение в очередь '{queue_name}' после {retry} попыток"
    )
    return False
