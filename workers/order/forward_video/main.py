import asyncio
from functools import partial

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from src.application.use_cases.forward_video_to_admin_use_case import (
    ForwardVideoToAdminUseCase,
)
from src.core.config.settings import settings
from src.core.setup_logging import setup_logging
from src.infrastructure.rabbitmq.consumer import QueueConsumer
from src.infrastructure.ya_disk.client import YandexDiskService
from src.notification_service.services.telegram_notifier import TelegramNotifier


async def handle_video_task(task_data: dict, bot: Bot, admin_chat_id: int):
    notifier = TelegramNotifier(bot=bot)

    use_case = ForwardVideoToAdminUseCase(
        notifier=notifier,
        admin_chat_id=admin_chat_id,
    )

    await use_case.execute(
        order_id=task_data["order_id"],
        file_id=task_data["file_id"],
        message_thread_id=settings.MEDIA_NOTIFICATION_THREAD,
    )


async def run_video_generation_worker():
    """
    Запуск потребителя очереди задач.
    """
    setup_logging(service_name="forward_video")

    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    storage_service = YandexDiskService(token=settings.YANDEX_TOKEN)

    try:
        consumer = QueueConsumer(
            queue_name="forward_video",
            handler_func=partial(
                handle_video_task,
                bot=bot,
                admin_chat_id=settings.ADMIN_CHAT_ID,
            ),
        )

        await consumer.start()

    finally:
        await bot.session.close()
        if hasattr(storage_service, "close"):
            await storage_service.close()


if __name__ == "__main__":
    asyncio.run(run_video_generation_worker())
