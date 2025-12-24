import asyncio
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from sqlalchemy import select
from telethon import TelegramClient

from src.application.dto.video_generation_task import VideoGenerationTask
from src.application.use_cases.generate_video_use_case import (
    GenerateAndUploadVideoUseCase,
)
from src.core.config.settings import settings
from src.core.setup_logging import setup_logging
from src.database.models.video_tasks import VideoTaskORM, VideoStatus
from src.database.uow import UnitOfWork
from src.infrastructure.telegram.telegram_media_service import TelegramMediaService
from src.infrastructure.video.moviepy_video_service import MoviePyVideoService
from src.infrastructure.ya_disk.client import YandexDiskService

log = logging.getLogger(__name__)

CHECK_INTERVAL = 60  # секунд между проверками БД


async def send_video(file_path: str, caption: str):
    try:
        async with TelegramClient("bot", settings.API_ID, settings.API_HASH) as client:
            await client.start(bot_token=settings.BOT_TOKEN)
            await client.send_file(
                entity=settings.ADMIN_CHAT_ID,
                file=file_path,
                caption=caption,
                reply_to=settings.MEDIA_NOTIFICATION_THREAD,
            )
    except Exception as e:
        log.error(f"Ошибка при отправке видео: {e}", exc_info=True)


async def handle_video_generation_task(
    task_orm: VideoTaskORM, bot: Bot, storage_service: YandexDiskService
):
    """
    Обрабатывает одну задачу генерации видео.
    Меняет статус задачи и логирует результат.
    """
    async with UnitOfWork() as uow:
        db_task = await uow.session.get(VideoTaskORM, task_orm.id)
        if not db_task or db_task.status != VideoStatus.pending:
            return

        db_task.status = VideoStatus.processing
        await uow.commit()

    try:
        task = VideoGenerationTask(**task_orm.params)

        video_use_case = GenerateAndUploadVideoUseCase(
            telegram_service=TelegramMediaService(bot=bot),
            video_service=MoviePyVideoService(),
            storage_service=storage_service,
        )

        output_path = await video_use_case.execute(
            order_id=task.order_id,
            file_ids=task.files,
            output_path=task.output_path,
        )

        log.info("Начинаем отправлять видео...")
        log.info(output_path)
        await send_video(
            file_path=output_path.video_path,
            caption=f"Видео для заказа #{task.order_id}",
        )

        log.info("Видео отправлено")

        async with UnitOfWork() as uow:
            db_task = await uow.session.get(VideoTaskORM, task_orm.id)
            db_task.status = VideoStatus.done
            await uow.commit()

        log.info(f"✅ Видео успешно сгенерировано для задачи {task_orm.id}")

    except Exception as e:
        log.exception(f"❌ Ошибка при обработке задачи {task_orm.id}: {e}")
        async with UnitOfWork() as uow:
            db_task = await uow.session.get(VideoTaskORM, task_orm.id)
            db_task.status = VideoStatus.error
            await uow.commit()


async def run_video_generation_worker():
    """
    Основной цикл воркера — проверяет базу и запускает задачи.
    """
    setup_logging(service_name="generate_video")
    log.info("🚀 Запуск видео-воркера")

    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    storage_service = YandexDiskService(token=settings.YANDEX_TOKEN)

    stop_event = asyncio.Event()

    async def shutdown():
        log.info("🛑 Завершение работы воркера...")
        stop_event.set()

    # Позволяет Ctrl+C завершить работу корректно

    try:
        while True:
            async with UnitOfWork() as uow:
                result = await uow.session.execute(
                    select(VideoTaskORM).where(
                        VideoTaskORM.status == VideoStatus.pending
                    )
                )
                video_tasks = result.scalars().all()

            if video_tasks:
                log.info(f"📦 Найдено {len(video_tasks)} задач для обработки")
                for task in video_tasks:
                    await handle_video_generation_task(task, bot, storage_service)
            else:
                log.debug("📭 Новых задач не найдено")

            await asyncio.sleep(CHECK_INTERVAL)

    finally:
        await bot.session.close()
        if hasattr(storage_service, "close"):
            await storage_service.close()
        log.info("✅ Воркер успешно завершён.")


if __name__ == "__main__":
    asyncio.run(run_video_generation_worker())
