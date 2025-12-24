import asyncio
import base64
import logging
from datetime import datetime
from typing import Optional

from aiogram import Bot
from jinja2 import Template
from pydantic import BaseModel
from sqlalchemy import select, and_, func

from src.application.dto.video_generation_task import VideoGenerationTask
from src.core.config.settings import settings
from src.core.database.async_session import AsyncSessionLocal
from src.core.setup_logging import setup_logging
from src.database.models import (
    WbAssemblyTaskORM,
    WbOrderORM,
    MaterialORM,
    TemplateORM,
    CategoryORM,
    SupplyORM,
    CategorySupplyCounterORM,
    CategorySettingsORM,
    VideoTaskORM,
)
from src.database.models.video_tasks import VideoStatus
from src.infrastructure.rabbitmq.consumer import QueueConsumer
from src.infrastructure.rabbitmq.producer import send_to_queue
from src.infrastructure.wb_service.client import WBApiService
from src.infrastructure.ya_disk.client import YandexDiskService

log = logging.getLogger(__name__)
wb_client = WBApiService(api_key=settings.WB_TOKEN)
yandex_disk = YandexDiskService(token=settings.YANDEX_TOKEN)
bot = Bot(token=settings.BOT_TOKEN)


class SupplyTask(BaseModel):
    assembly_task_id: int


async def send_skip_video_message(assembly_task_id: int, reason: Optional[str] = None):
    text = f"❌ Видео для заказа {assembly_task_id} отсутствует.\n"

    if reason:
        text += reason

    try:
        await bot.send_message(
            chat_id=settings.ADMIN_CHAT_ID,
            message_thread_id=settings.MEDIA_NOTIFICATION_THREAD,
            text=text,
        )
    except Exception as e:
        log.error("Ошибка при отправке сообщения в чат: %s", e, exc_info=True)


async def render_template(text, **context):
    template = Template(text)

    now = datetime.now()
    context.update(
        {
            "year": now.year,
            "month": f"{now.month:02}",
            "day": f"{now.day:02}",
            "hour": f"{now.hour:02}",
            "minute": f"{now.minute:02}",
            "second": f"{now.second:02}",
        }
    )

    return template.render(**context)


async def processing_supply(data: dict):
    task = SupplyTask.model_validate(data)

    async with AsyncSessionLocal() as session:
        assembly_task = await session.get(WbAssemblyTaskORM, task.assembly_task_id)

        if not assembly_task:
            log.error(
                "Сборочное задание с id %s не найдено в базе данных",
                task.assembly_task_id,
            )
            raise ValueError(
                f"Сборочное задание с id {task.assembly_task_id} не найдено"
            )

        if assembly_task.supply_id:
            log.info(
                "Сборочное задание с id %s уже имеет поставку",
                task.assembly_task_id,
            )
            raise ValueError(
                f"Сборочное задание с id {task.assembly_task_id} уже имеет поставку"
            )

        wb_order = await session.get(WbOrderORM, assembly_task.wb_order_id)

        if not wb_order:
            log.error(
                "Заказ с id %s не найден в базе данных", assembly_task.wb_order_id
            )
            raise ValueError(f"Заказ с id {assembly_task.wb_order_id} не найден")

        material = await session.scalar(
            select(MaterialORM).where(MaterialORM.id == wb_order.material_id)
        )

        if not material:
            log.error("Материал с id %s не найден в базе данных", wb_order.material_id)
            raise ValueError(f"Материал с id {wb_order.material_id} не найден")

        template = await session.get(TemplateORM, material.template_id)

        if not template:
            log.error("Шаблон с id %s не найден в базе данных", material.template_id)
            raise ValueError(f"Шаблон с id {material.template_id} не найден")

        category = await session.get(CategoryORM, template.category_id)

        if not category:
            log.error(
                "Категория с id %s не найдена в базе данных", template.category_id
            )
            raise ValueError(f"Категория с id {template.category_id} не найдена")

        query = select(CategorySettingsORM).where(
            CategorySettingsORM.category_id == category.id
        )
        result = await session.execute(query)

        category_settings: CategorySettingsORM = result.scalar_one_or_none()

        supply = await session.scalar(
            select(SupplyORM)
            .with_for_update()
            .where(
                and_(
                    SupplyORM.category_name == category.name,
                    SupplyORM.order_count < 10,
                    SupplyORM.status == "active",
                )
            )
        )

        if not supply:
            category_supply_counter = await session.scalar(
                select(CategorySupplyCounterORM).where(
                    CategorySupplyCounterORM.category_name == category.name,
                )
            )
            if not category_supply_counter:
                category_supply_counter = CategorySupplyCounterORM(
                    category_name=category.name,
                )
                session.add(category_supply_counter)
                await session.flush()

            category_supply_counter.supply_count += 1
            await session.flush()

            wb_supply_name = f"{category.name} - {category_supply_counter.supply_count}"
            wb_supply = await wb_client.create_supply(name=wb_supply_name)

            supply = SupplyORM(
                id=wb_supply.id,
                category_name=category.name,
                name=wb_supply_name,
                order_count=0,
            )

            session.add(supply)
            await session.flush()
            await session.refresh(supply)

        else:
            await session.refresh(supply, with_for_update=True)

        await wb_client.add_assembly_task_to_supply(
            supply_id=str(supply.id), assembly_task_id=assembly_task.id
        )

        assembly_task.supply_id = supply.id
        assembly_task.added_to_supply_at = func.now()

        log.info("Получен стикер для сборочного задания %s", assembly_task.id)

        assembly_task_stickers = await wb_client.get_assembly_task_stickers(
            assembly_task_ids=[assembly_task.id]
        )

        sticker = assembly_task_stickers.stickers[0]
        image_data = base64.b64decode(sticker.file)

        category_folder = category.folder_name or "unsorted"

        folder_path = await render_template(
            text=category_settings.output_path,
            category_folder=category_folder,
            order_date=wb_order.created_at.date(),
            assembly_task_id=assembly_task.id,
            supply_name=supply.name,
        )

        file_name = "sticker.png"

        layout_file_name = (
            f"{sticker.part_b}-{wb_order.supplier_article}-{assembly_task.id}"
        )

        supply.order_count += 1

        if supply.order_count >= 10:
            supply.status = "inactive"
            await session.flush()

        if category_settings.save_as_format:
            await yandex_disk.upload_bytes(image_data, f"{folder_path + file_name}")

        await send_to_queue(
            queue_name="generate_image",
            data={
                "type": "pdf",
                "delivery": {
                    "method": "ya_disk",
                    f"path": folder_path,
                    "assembly_task": assembly_task.id,
                    "supplier_article": wb_order.supplier_article,
                },
                "order_data": material.data.get("layout"),
                "template_id": material.template_id,
                "filename": layout_file_name,
            },
        )

        if material.data.get("video"):
            video = material.data.get("video")
            action = video.get("action")

            if action == "forward_video":
                await send_to_queue(
                    queue_name="forward_video",
                    data={
                        "order_id": assembly_task.id,
                        "file_id": video.get("video").get("video_id"),
                    },
                )
            elif action == "generate_video":
                files = [file.get("photo_url") for file in video.get("photo", [])]

                if not files:
                    await send_skip_video_message(
                        assembly_task_id=assembly_task.id,
                        reason="⚠️ Пользователь выбрал генерацию видео, но не прикрепил файлы",
                    )
                    return

                # await send_to_queue(
                #     queue_name="generate_video",
                #     data=VideoGenerationTask(
                #         order_id=assembly_task.id, files=files, output_path=folder_path
                #     ).model_dump(),
                # )
                # Формируем DTO
                task_data = VideoGenerationTask(
                    order_id=assembly_task.id,
                    files=files,
                    output_path=folder_path,
                )

                # Сохраняем задачу напрямую в БД
                video_task = VideoTaskORM(
                    params=task_data.model_dump(),
                    status=VideoStatus.pending,
                )
                session.add(video_task)

                log.info(
                    f"🧩 Новая видео-задача сохранена в БД: {video_task.id} (order_id={assembly_task.id})"
                )

            elif action == "skip_video":
                await send_skip_video_message(
                    assembly_task_id=assembly_task.id,
                    reason="⚠️ Пользователь нажал кнопку пропустить видео",
                )
            else:
                log.info(
                    f"⏭️ Пропускаем видео для сборочного задания {assembly_task.id}"
                )

        await session.commit()


async def main():
    worker = QueueConsumer(
        queue_name="processing_supply",
        handler_func=processing_supply,
    )

    await worker.start()


if __name__ == "__main__":
    setup_logging(service_name="processing_supply")
    asyncio.run(main())
