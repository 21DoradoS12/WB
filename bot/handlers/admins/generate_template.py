import logging
import time

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database.models import WbAssemblyTaskORM, WbOrderORM, MaterialORM
from src.database.uow import UnitOfWork
from src.infrastructure.rabbitmq.producer import send_to_queue

router = Router()
log = logging.getLogger(name=__name__)


@router.message(Command("generate_template"))
async def generate_template(message: Message, command: CommandObject, uow: UnitOfWork):
    assembly_task_id = int(command.args)

    assembly_task = await uow.session.scalar(
        select(WbAssemblyTaskORM).where(WbAssemblyTaskORM.id == assembly_task_id)
    )

    if not assembly_task:
        return await message.answer("Ошибка! Не найден сборочный лист с таким ID.")

    wb_order = await uow.session.scalar(
        select(WbOrderORM).where(WbOrderORM.id == assembly_task.wb_order_id)
    )

    if not wb_order:
        return await message.answer("Ошибка! Не найден заказ с таким ID.")

    material = await uow.session.scalar(
        select(MaterialORM).where(MaterialORM.id == wb_order.material_id)
    )

    if not material:
        return await message.answer(f"Ошибка! Не найден шаблон для заказа.")

    folder_path = f"giftoboom/admins/{assembly_task_id}/"
    file_name = f"{assembly_task_id}"

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
            "order_data": material.data,
            "template_id": material.template_id,
            "filename": file_name,
        },
    )

    return await message.answer("Файл отправлен на генерацию.")


@router.message(Command("generate_supply_template"))
async def generate_template(message: Message, command: CommandObject, uow: UnitOfWork):
    start_time = time.perf_counter()

    if not command.args:
        log.warning(
            "Вызвана команда без аргументов", extra={"user_id": message.from_user.id}
        )
        return await message.answer(
            "Ошибка! Не указан ID поставки. Пример: /generate_supply_template 1"
        )

    supply_id = command.args.strip()

    log.info(
        "Запрос на генерацию шаблонов",
        extra={"user_id": message.from_user.id, "supply_id": supply_id},
    )

    # загружаем assembly_tasks + order + material за один проход
    result = await uow.session.execute(
        select(WbAssemblyTaskORM)
        .where(WbAssemblyTaskORM.supply_id == supply_id)
        .options(
            selectinload(WbAssemblyTaskORM.wb_order).selectinload(WbOrderORM.material)
        )
    )
    assembly_tasks = result.scalars().all()

    if not assembly_tasks:
        log.error(
            "Не найдено сборочных листов для поставки",
            extra={"user_id": message.from_user.id, "supply_id": supply_id},
        )
        return await message.answer(
            f"Ошибка! Не найдено сборочных листов для поставки {supply_id}."
        )

    errors, success_count = [], 0

    for assembly_task in assembly_tasks:
        wb_order = assembly_task.wb_order
        material = wb_order.material if wb_order else None

        if not wb_order:
            msg = f"Не найден заказ WB для сборочного листа {assembly_task.id}"
            log.error(msg, extra={"assembly_task_id": assembly_task.id})
            errors.append(msg)
            continue

        if not material or not material.data or not material.template_id:
            msg = f"Не найден или некорректный материал для сборочного листа {assembly_task.id}"
            log.error(msg, extra={"assembly_task_id": assembly_task.id})
            errors.append(msg)
            continue

        folder_path = f"giftoboom/admins/{supply_id}/{assembly_task.id}/"
        file_name = f"{assembly_task.id}"

        task_payload = {
            "type": "pdf",
            "delivery": {
                "method": "ya_disk",
                "path": folder_path,
                "assembly_task": assembly_task.id,
                "supplier_article": wb_order.supplier_article,
            },
            "order_data": material.data,
            "template_id": material.template_id,
            "filename": file_name,
        }

        try:
            await send_to_queue("generate_image", data=task_payload)
            log.info(
                "Отправлена задача в очередь",
                extra={
                    "supply_id": supply_id,
                    "assembly_task_id": assembly_task.id,
                    "user_id": message.from_user.id,
                },
            )
            success_count += 1
        except Exception as e:
            msg = f"Ошибка отправки задачи {assembly_task.id}: {e}"
            log.exception(
                "Ошибка при отправке в очередь",
                extra={"assembly_task_id": assembly_task.id, "supply_id": supply_id},
            )
            errors.append(msg)

    duration = time.perf_counter() - start_time
    text = (
        f"✅ Успешно отправлено {success_count} шаблон(ов) на генерацию."
        if not errors
        else f"Успешно отправлено {success_count} шаблон(ов).\n\nОшибки:\n"
        + "\n".join(errors)
    )

    log.info(
        "Завершена обработка команды",
        extra={
            "supply_id": supply_id,
            "user_id": message.from_user.id,
            "success": success_count,
            "errors": len(errors),
            "duration_sec": round(duration, 2),
        },
    )

    return await message.answer(text)
