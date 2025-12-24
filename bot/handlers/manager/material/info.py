from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from src.application.use_cases.material.get_material_info import GetMaterialInfoUseCase
from src.application.use_cases.material.get_material_info_by_assembly_task_use_case import (
    GetMaterialInfoByAssemblyTaskUseCase,
)
from src.bot.keyboards.manager import material_action_keyboard
from src.database.uow import UnitOfWork

router = Router()


@router.message(Command("m"))
async def show_material_info(
    message: Message,
    command: CommandObject,
    uow: UnitOfWork,
):
    if not command.args:
        await message.reply("❗ Укажите ID материала. Пример: /m 42")
        return

    try:
        material_id = int(command.args)
    except ValueError:
        await message.reply("⚠️ ID материала должен быть числом.")
        return

    use_case = GetMaterialInfoUseCase(
        user_repo=uow.user,
        material_repo=uow.material,
        wb_order_repo=uow.wb_order,
        wb_assembly_task_repo=uow.wb_assembly_task,
        supply=uow.supply,
        template_repo=uow.template,
    )

    material_info = await use_case.execute(material_id=material_id)
    if not material_info:
        await message.reply(f"❌ Материал с ID={material_id} не найден")
        return

    user = material_info.user
    user_text = (
        (
            f"<b>👤 Пользователь:</b>\n"
            f" - ID: {getattr(user, 'id', 'Отсутствует')}\n"
            f" - Username: {getattr(user, 'username', 'Отсутствует')}\n"
            f" - Имя: {getattr(user, 'first_name', 'Отсутствует')}\n"
        )
        if user
        else "👤 Пользователь: отсутствует\n"
    )
    template = material_info.template
    template_text = f"<b>🖼 Название шаблона:</b> {template.name or 'Отсутствует'}"

    available_layers = []

    for key, value in material_info.data.items():
        action = value.get("action")
        if action is not None and "skip" not in action:
            available_layers.append(key)

    available_layers_text = "<b>Доступные слои:</b>\n"

    available_layers_text += "\n".join(available_layers)

    order = material_info.order
    if order:
        order_text = f"<b>🔗 Связь с Wildberries:</b>\n - WB ID: {getattr(order, 'id', 'Отсутствует')}\n"

        assembly_task = getattr(order, "assembly_task", None)
        if assembly_task:
            order_text += (
                f" - Сборочный номер: {getattr(assembly_task, 'id', 'Отсутствует')}\n"
            )

            supply = getattr(assembly_task, "supply", None)
            if supply:
                order_text += f" - Сборка: {getattr(supply, 'name', 'Отсутствует')}\n"
            else:
                order_text += " - Сборка: отсутствует\n"
        else:
            order_text += " - Сборочный номер: отсутствует\n"
    else:
        order_text = "🔗 Связь с Wildberries: отсутствует\n"

    text = f"📦 Материал #{material_info.id}\n\n{template_text}\n\n{available_layers_text}\n\n{user_text}\n{order_text}"

    keyboard = material_action_keyboard(material_info)

    await message.reply(text, reply_markup=keyboard)


@router.message(Command("s"))
async def show_material_info_by_assembly_task(
    message: Message,
    command: CommandObject,
    uow: UnitOfWork,
):
    if not command.args:
        await message.reply("❗ Укажите ID сборочного задания. Пример: /ma 123")
        return

    try:
        assembly_task_id = int(command.args)
    except ValueError:
        await message.reply("⚠️ ID сборочного задания должен быть числом.")
        return

    use_case = GetMaterialInfoByAssemblyTaskUseCase(
        material_repo=uow.material,
        user_repo=uow.user,
        template_repo=uow.template,
        wb_assembly_task_repo=uow.wb_assembly_task,
        wb_order_repo=uow.wb_order,
        supply_repo=uow.supply,
    )

    material_info = await use_case.execute(assembly_task_id=assembly_task_id)
    if not material_info:
        await message.reply(
            f"❌ Материал для сборочного задания ID={assembly_task_id} не найден"
        )
        return

    user = material_info.user
    user_text = (
        (
            f"<b>👤 Пользователь:</b>\n"
            f" - ID: {getattr(user, 'id', 'Отсутствует')}\n"
            f" - Username: {getattr(user, 'username', 'Отсутствует')}\n"
            f" - Имя: {getattr(user, 'first_name', 'Отсутствует')}\n"
        )
        if user
        else "👤 Пользователь: отсутствует\n"
    )
    template = material_info.template
    template_text = f"<b>🖼 Название шаблона:</b> {template.name or 'Отсутствует'}"

    available_layers = []

    for key, value in material_info.data.items():
        action = value.get("action")
        if action is not None and "skip" not in action:
            available_layers.append(key)

    available_layers_text = "<b>Доступные слои:</b>\n"
    available_layers_text += "\n".join(available_layers)

    order = material_info.order
    if order:
        order_text = f"<b>🔗 Связь с Wildberries:</b>\n - WB ID: {getattr(order, 'id', 'Отсутствует')}\n"
        assembly_task = getattr(order, "assembly_task", None)
        if assembly_task:
            order_text += (
                f" - Сборочный номер: {getattr(assembly_task, 'id', 'Отсутствует')}\n"
            )
            supply = getattr(assembly_task, "supply", None)
            if supply:
                order_text += f" - Сборка: {getattr(supply, 'name', 'Отсутствует')}\n"
            else:
                order_text += " - Сборка: отсутствует\n"
        else:
            order_text += " - Сборочный номер: отсутствует\n"
    else:
        order_text = "🔗 Связь с Wildberries: отсутствует\n"

    text = f"📦 Материал #{material_info.id}\n\n{template_text}\n\n{available_layers_text}\n\n{user_text}\n{order_text}"

    keyboard = material_action_keyboard(material_info)

    await message.reply(text, reply_markup=keyboard)
