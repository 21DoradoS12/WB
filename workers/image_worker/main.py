import asyncio
import io
import json
import logging

from PIL import Image
from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.core.config.settings import settings
from src.core.setup_logging import setup_logging
from src.database.uow import UnitOfWork
from src.infrastructure.rabbitmq.consumer import QueueConsumer
from src.infrastructure.ya_disk.client import YandexDiskService
from src.workers.image_worker.generator.generate_output_from_template import (
    generate_output_from_template,
)
from src.workers.image_worker.schemas import GenerateTask
from src.workers.image_worker.services.telegram_service import send_to_telegram

bot = Bot(token=settings.BOT_TOKEN)
yandex_disk = YandexDiskService(token=settings.YANDEX_TOKEN)
log = logging.getLogger(__name__)


def mm_to_px(mm: float, dpi: int = 500, scalar: float = 1.0) -> int:
    """Перевод миллиметров в пиксели."""
    return int(mm / 25.4 * dpi * scalar)


def resize_image_bytes(image_bytes: bytes, size: tuple[int, int]) -> bytes:
    """
    Изменяет размер изображения, представленного в виде байтов.

    :param image_bytes: исходное изображение в формате bytes
    :param size: кортеж (ширина, высота), например (800, 600)
    :return: изменённое изображение в формате bytes
    """
    # Открываем изображение из байтов
    with Image.open(io.BytesIO(image_bytes)) as img:
        # Конвертируем в RGB, если нужно (например, для .jpg)
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        # Изменяем размер
        resized_img = img.resize(size, Image.Resampling.LANCZOS)

        # Сохраняем в буфер
        buffer = io.BytesIO()
        resized_img.save(
            buffer, format="JPEG", quality=85
        )  # или 'PNG', если нужно прозрачность

        # Возвращаем байты
        return buffer.getvalue()


async def processing_image(data: dict):
    task = GenerateTask(**data)

    try:
        async with UnitOfWork() as uow:
            template = await uow.template.get_template_by_id(
                template_id=task.template_id
            )

            if not template:
                return

            if task.delivery:
                delivery = task.delivery
                method = delivery.get("method")
                if method == "telegram":
                    file_io = await generate_output_from_template(
                        bot=bot,
                        order_data=task.order_data,
                        template_json=template.template_json,
                        scalar=1,
                        output_format=task.type,
                        dpi=task.dpi,
                    )
                    filename = (
                        f"{task.filename}.{task.type}"
                        if task.filename
                        else f"image.{task.type}"
                    )

                    file_bytes = file_io.getvalue()

                    chat_id = delivery.get("chat_id")

                    kb = InlineKeyboardBuilder()
                    kb.button(text="Подтвердить", callback_data="confirm")
                    kb.button(text="Начать с начала", callback_data="restart_template")
                    kb.adjust(1)

                    text = (
                        "Подтверждая макет, вы соглашаетесь с тем, что:\n\n"
                        "• фото, надписи, цвета и расположение отображаются именно так, как вы хотите;\n"
                        "• качество исходных фотографий и их пригодность для печати — ваша ответственность;\n"
                    )

                    await send_to_telegram(
                        bot=bot,
                        text=text,
                        chat_id=chat_id,
                        file_bytes=file_bytes,
                        filename=filename,
                        as_photo=True,
                        reply_markup=kb.as_markup(),
                    )

                elif method == "ya_disk":
                    category = await uow.category.get_by_id(
                        category_id=template.category_id
                    )

                    category_settings = await uow.category_settings.get_by_category_id(
                        category_id=category.id
                    )

                    file_io = await generate_output_from_template(
                        bot=bot,
                        order_data=task.order_data,
                        template_json=template.template_json,
                        scalar=1,
                        output_format=category.save_as_format,
                        dpi=task.dpi,
                    )

                    filename = (
                        f"{task.filename}.{category.save_as_format}"
                        if task.filename
                        else f"image.{task.type}"
                    )

                    file_bytes = file_io.getvalue()

                    # Загрузка макета на диск
                    path = delivery.get("path")

                    assembly_task = delivery.get("assembly_task")
                    supplier_article = delivery.get("supplier_article")

                    await yandex_disk.upload_bytes(
                        data=file_bytes,
                        yandex_path=path + filename,
                    )

                    if category_settings.save_original_data:

                        for d, data in task.order_data.items():
                            if isinstance(data, dict):
                                if data.get("photo_url"):
                                    photo_url = data.get("photo_url")
                                    file = await bot.get_file(photo_url)
                                    photo_bytes = await bot.download_file(
                                        file.file_path
                                    )

                                    elements = template.template_json.get("elements")
                                    for element in elements:
                                        if element.get("name") == d:
                                            photo_position = element.get("position")
                                            break

                                    width = mm_to_px(int(photo_position["width"]))
                                    height = mm_to_px(int(photo_position["height"]))

                                    photo_bytes = resize_image_bytes(
                                        photo_bytes.read(), (width, height)
                                    )
                                    await yandex_disk.upload_bytes(
                                        data=photo_bytes,
                                        yandex_path=f"{path}{d}.png",
                                    )

                        json_bytes = json.dumps(
                            task.order_data, ensure_ascii=False, indent=4
                        ).encode("utf-8")

                        await yandex_disk.upload_bytes(
                            data=json_bytes,
                            yandex_path=path + "Данные" + ".json",
                        )
    except Exception as e:
        log.error("Ошибка при обработке задачи %s: %s", task, e, exc_info=True)


async def main():
    worker = QueueConsumer(
        queue_name="generate_image",
        handler_func=processing_image,
    )

    await worker.start()


if __name__ == "__main__":
    setup_logging(service_name="image_generate_worker")
    asyncio.run(main())
