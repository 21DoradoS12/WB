import asyncio
import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from src.bot.keyboards.user import (
    generate_select_option_keyboard,
    get_order_already_done_keyboard,
)
from src.bot.states import TemplateFormStates
from src.database.models import MaterialORM
from src.database.uow import UnitOfWork
from src.infrastructure.rabbitmq.producer import send_to_queue

log = logging.getLogger(__name__)


def expand_steps(form_steps: list, prefix: str = "") -> list:
    expanded = []
    for step in form_steps:
        step_type = step.get("type")
        step_name = step.get("name")
        full_name = f"{prefix}.{step_name}" if prefix else step_name

        if step_type == "group":
            repeat_count = step.get("repeat_count", 1)
            sub_steps = step.get("steps", [])
            log.debug(
                "Раскрытие группы шагов '%s' (%s повторов)", full_name, repeat_count
            )
            for i in range(repeat_count):
                expanded.extend(expand_steps(sub_steps, prefix=f"{full_name}.{i}"))
        else:
            step_copy = step.copy()
            step_copy["name"] = full_name
            expanded.append(step_copy)
            log.debug("Добавлен шаг: %s (%s)", full_name, step_type)
    return expanded


def collapse_data(flat_data: dict) -> dict:
    result = {}
    log.debug("Начало сворачивания данных: %s", flat_data.keys())

    for key, value in flat_data.items():
        parts = key.split(".")
        if len(parts) < 3:
            result[key] = value
            log.debug("Сохраняем простой ключ: %s=%s", key, value)
            continue

        group = parts[0]
        index = int(parts[1])
        nested_keys = parts[2:]

        if group not in result:
            result[group] = []

        while len(result[group]) <= index:
            result[group].append({})

        current = result[group][index]
        for k in nested_keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]

        current[nested_keys[-1]] = value
        log.debug("Собран вложенный ключ: %s -> %s", key, value)

    return result


async def validate_message_for_step(message: Message, state: FSMContext) -> bool:

    step_data = await state.get_data()
    current_step = step_data.get("current_step")

    if not current_step:
        log.warning("У пользователя %s не найден текущий шаг", message.from_user.id)
        await message.answer("Произошла ошибка. Попробуйте сначала /start")
        await state.clear()
        return False

    step_type = current_step.get("type")
    log.info(
        "Проверка сообщения от пользователя %s на шаге '%s' (%s)",
        message.from_user.id,
        current_step.get("name"),
        step_type,
    )

    if step_type == "select":
        await message.answer(
            text=f"Необходимо выбрать один из вариантов:",
        )
        return False

    elif step_type == "photo":
        if not message.photo:
            await message.answer("Пожалуйста, отправьте фото.")
            return False

    elif step_type == "text":
        if not message.text or message.from_user.is_bot:
            await message.answer("Пожалуйста, отправьте текст.")
            return False

    elif step_type == "multi":
        # Проверяем наличие фото ИЛИ медиагруппы
        has_photo = message.photo is not None and len(message.photo) > 0
        has_media_group = message.media_group_id is not None

        # Если есть медиагруппа, но фото еще нет - это нормально, ждем следующие сообщения
        if has_media_group and not has_photo:
            # Пропускаем это сообщение, ждем следующее с фото
            return True

        # Если нет ни фото, ни медиагруппы - ошибка
        if not has_photo and not has_media_group:
            await message.answer("Пожалуйста, отправьте фото.")
            return False

    elif step_type == "media":
        has_photo = message.photo is not None and len(message.photo) > 0
        has_video = message.video is not None
        has_media_group = message.media_group_id is not None

        if has_media_group:
            return True

        if not has_photo and not has_video:
            await message.answer("Пожалуйста, отправьте фото или видео.")
            return False

    elif step_type == "video":
        if not message.video:
            await message.answer("Пожалуйста, отправьте видео.")
            return False

    return True


async def process_next_step(
    message: Message,
    state: FSMContext,
    uow: UnitOfWork,
) -> None:
    data = await state.get_data()

    # --- Извлечение и валидация данных состояния ---
    steps = data.get("_steps", [])
    step_index = data.get("_step_index", 0)
    groups = data.get("_groups", [])
    group_index = data.get("_group_index", 0)
    all_steps = data.get("_all_steps", [])

    step_text = f"<b>📋 Шаг [{step_index+1}/{len(steps)}]</b>\n\n"

    # Защита от пустых/некорректных данных
    if not isinstance(groups, list) or not groups:
        log.error(
            "Список групп пуст или отсутствует для пользователя %s",
            message.from_user.id,
        )
        await message.answer("⚠️ Ошибка конфигурации. Обратитесь в поддержку.")
        return

    if group_index < 0 or group_index >= len(groups):
        log.error(
            "Некорректный group_index=%s для groups=%s у пользователя %s",
            group_index,
            groups,
            message.from_user.id,
        )
        await message.answer("⚠️ Ошибка состояния. Попробуйте начать заново.")
        return

    current_group = groups[group_index]
    group_name = current_group.get("name")
    user_data = data.get("data", {})

    # --- Логика перехода: если текущие шаги закончились ---
    if step_index >= len(steps):
        log.info(
            "Пользователь %s завершил все шаги в группе %s",
            message.from_user.id,
            group_name,
        )
        group_index += 1

        # Проверяем, не вышли ли за пределы групп
        if group_index >= len(groups):
            log.info(
                "Пользователь %s завершил все группы. Переходим к финалу.",
                message.from_user.id,
            )
            await finalize_order(message, state, uow)
            return

        # Защита: проверяем, что all_steps существует и имеет нужный индекс
        if not isinstance(all_steps, list) or group_index >= len(all_steps):
            log.error(
                "Некорректная структура all_steps: %s, запрашиваем индекс %s",
                all_steps,
                group_index,
            )
            await message.answer("⚠️ Ошибка конфигурации. Обратитесь в поддержку.")
            return

        await message.answer(
            f"✅ Этап {group_index} завершён! Приступаем к следующему."
        )

        await asyncio.sleep(2)

        # Инициализируем шаги новой группы
        step_index = 0
        steps = expand_steps(all_steps[group_index].get("steps", []))

        current_group = groups[group_index]
        group_name = current_group.get("name")
        group_action = current_group.get("action")
        group_data = user_data.setdefault(group_name, {})

        if group_action:
            group_data["action"] = group_action

        # Обновляем состояние — только изменённые поля
        await state.update_data(
            {
                "data": user_data,
                "_group_index": group_index,
                "_steps": steps,
                "_step_index": step_index,
            }
        )

        # Рекурсивно вызываем обработку первого шага новой группы
        # (все данные уже обновлены, повторно вызываем ту же функцию)
        return await process_next_step(message, state, uow)

    # --- Обработка текущего шага ---
    if not steps or step_index < 0 or step_index >= len(steps):
        log.error(
            "Некорректный step_index=%s для steps=%s у пользователя %s",
            step_index,
            steps,
            message.from_user.id,
        )
        await message.answer("⚠️ Ошибка состояния шага. Попробуйте начать заново.")
        return

    step = steps[step_index]

    # Обновляем состояние: текущий шаг + FSM состояние
    await state.update_data({"current_step": step})
    await state.set_state(TemplateFormStates.WaitingStep)

    log.info(
        "Пользователь %s перешел к шагу %s (%s)",
        message.from_user.id,
        step.get("name", "безымянный"),
        step.get("type", "неизвестный"),
    )

    # --- Отправка контента по типу шага ---
    step_text += step.get("text", "")
    step_type = step.get("type")

    if step_type == "select":
        options = step.get("options", [])
        keyboard = generate_select_option_keyboard(options=options)
        await message.answer(step_text, reply_markup=keyboard)
        return

    elif step_type == "generate_image":
        order_data = collapse_data(user_data.get(group_name, {}))
        template_id = data.get("template_id")

        success = await handle_generation_step(
            order_data=order_data,
            template_id=template_id,
            user_id=message.from_user.id,
        )

        if not success:
            await message.answer(
                "⚠️ Произошла ошибка при подготовке изображения.\n"
                "Пожалуйста, попробуйте позже или обратитесь в поддержку."
            )
            return

        await message.answer(
            f"{step_text}"
            "🎨 Ваше изображение уже в работе!\n"
            "Обычно это занимает несколько минут — мы пришлём его сюда, как только оно будет готово.\n\n"
            "⏳ Если изображение не пришло в течение 5–10 минут — напишите нам в поддержку."
        )
        await state.set_state(TemplateFormStates.Confirmed)
        return

    elif step_type in ["multi", "media"]:
        step_optional = step.get("optional")
        allow_early_finish = step.get("allow_early_finish")
        finish_button_text = step.get("finish_button_text")

        reply_markup = None

        if allow_early_finish:
            keyword = ReplyKeyboardBuilder()
            keyword.button(text=finish_button_text or "Завершить шаг")
            keyword.adjust(1)
            reply_markup = keyword.as_markup(
                resize_keyboard=True,
                one_time_keyboard=True,
                is_persistent=True,
            )

        if step_optional:
            step_text += "\nДанный шаг можно пропустить /skip."

        await message.answer(step_text, reply_markup=reply_markup)

        return None

    else:
        # Обычный шаг: текст или фото
        if step_type == "photo":
            step_text += " (Отправьте фото)"

        example = step.get("example")

        if not example:
            await message.answer(step_text)
            return

        ex_type = example.get("type")
        ex_source = example.get("source")
        ex_content = example.get("content")

        if not ex_content:
            await message.answer(step_text)
            return

        try:
            content = (
                FSInputFile(path=ex_content) if ex_source == "disk" else ex_content
            )

            if ex_type == "photo":
                await message.answer_photo(photo=content, caption=step_text)
            elif ex_type == "video":
                await message.answer_video(video=content, caption=step_text)
            elif ex_type == "document":
                await message.answer_document(document=content, caption=step_text)
            else:
                await message.answer(
                    f"{step_text}\n[Пример типа '{ex_type}' не поддерживается]"
                )
        except Exception as e:
            log.error("Ошибка при отправке примера: %s", e)
            await message.answer(step_text)


async def finalize_order(message: Message, state: FSMContext, uow: UnitOfWork):
    data = await state.get_data()
    flat_data = data.get("data", {})
    template_id = data.get("template_id")
    order_data = collapse_data(flat_data)

    new_material = MaterialORM(
        user_id=(
            message.from_user.id if not message.from_user.is_bot else message.chat.id
        ),
        template_id=template_id,
        data=order_data,
    )

    material = await uow.material.create(material=new_material)

    await state.clear()

    await message.answer(
        text=(
            f"✅ Ваш материал №{material.id} успешно сохранён!\n\n"
            f"Чтобы мы могли продолжить обработку, выполните два простых шага:\n"
            f"1. Оформите заказ на Wildberries\n"
            f"2. Нажмите кнопку: «МОЙ ЗАКАЗ УЖЕ ОФОРМЛЕН»\n\n"
            "📌 Важно: Для корректной обработки в нашей системе учитывается только <b>сразу оплаченный заказ</b>.\n"
            "Пожалуйста, оплатите товар сразу после оформления — это поможет избежать путаницы на стадии производства.\n"
        ),
        reply_markup=get_order_already_done_keyboard(material_id=material.id),
    )


async def handle_generation_step(
    order_data: dict,
    template_id: int,
    user_id: int,
) -> bool:
    """
    Отправляет данные для генерации изображения
    """
    try:
        await send_to_queue(
            queue_name="generate_image",
            data={
                "type": "png",
                "delivery": {"method": "telegram", "chat_id": user_id},
                "order_data": order_data,
                "template_id": template_id,
                "dpi": 200,
            },
        )
        log.info("Задача успешно отправлена в очередь для пользователя %s", user_id)
        return True

    except Exception as e:
        log.error(
            "Ошибка отправки задачи в очередь для пользователя %s",
            user_id,
            exc_info=e,
        )
        return False
