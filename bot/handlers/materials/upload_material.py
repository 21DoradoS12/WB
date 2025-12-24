import asyncio
import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, PhotoSize, InputMediaPhoto
from aiogram_album import AlbumMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.photo_validation import ImageInfo
from src.bot.states import TemplateFormStates
from src.bot.utils.upload_materials import (
    validate_message_for_step,
    expand_steps,
    process_next_step,
)
from src.bot.validators.image.factory import ImageValidatorFactory
from src.bot.validators.text.factory import TextValidatorFactory
from src.database.models import TemplateORM
from src.database.uow import UnitOfWork

router = Router(name=__name__)
log = logging.getLogger(__name__)


@router.message(TemplateFormStates.WaitingStep, Command("skip"))
async def handle_skip_step(
    message: Message,
    state: FSMContext,
    uow: UnitOfWork,
):
    """
    Обрабатывает команду пропуска текущего шага в многошаговом сценарии.
    Пропуск возможен только если шаг помечен как необязательный.
    """

    data = await state.get_data()
    current_step = data.get("current_step")

    if not current_step:
        await message.answer(
            "Невозможно определить текущий шаг. Пожалуйста, начните процесс заново."
        )
        return

    if not current_step.get("optional", False):
        await message.answer("Этот шаг обязателен — его нельзя пропустить.")
        return

    data["_step_index"] += 1

    await state.set_data(data)

    await message.answer("Шаг успешно пропущен.")
    await process_next_step(message, state, uow)


@router.message(TemplateFormStates.WaitingStep, F.text, ~F.photo)
async def handle_text_step(
    msg: Message,
    state: FSMContext,
    uow: UnitOfWork,
):
    step_data = await state.get_data()
    current_step = step_data.get("current_step")

    allow_early_finish = current_step.get("allow_early_finish")
    finish_button_text = current_step.get("finish_button_text")

    if allow_early_finish:
        if msg.text == finish_button_text:
            await msg.answer("Шаг успешно завершен.")
            step_data["_step_index"] += 1
            await state.set_data(step_data)
            await process_next_step(msg, state, uow)
            return None

    if not await validate_message_for_step(msg, state):
        return

    validators = TextValidatorFactory.create_validators(current_step.get("validators"))

    for validator in validators:
        try:
            result = await validator.validate(msg.text)
            if not result.is_valid:
                log.info(
                    "Валидация провалена",
                    extra={
                        "step_name": current_step.get("name"),
                        "validator_type": validator.__class__.__name__,
                        "user_input": msg.text,
                        "validation_error": result.error_text,
                        "user_id": msg.from_user.id,
                        "chat_id": msg.chat.id,
                    },
                )
                if validator.error_media_id and validator.error_media_type:
                    if validator.error_media_type == "photo":
                        await msg.reply_photo(
                            photo=validator.error_media_id,
                            caption=(
                                f"⚠️ {result.error_text}" if result.error_text else None
                            ),
                        )
                    elif validator.error_media_type == "video":
                        await msg.reply_video(
                            video=validator.error_media_id,
                            caption=(
                                f"⚠️ {result.error_text}" if result.error_text else None
                            ),
                        )
                else:
                    await msg.reply(text=f"⚠️ {result.error_text}")

                return
        except Exception as e:
            log.exception(
                "Исключение при выполнении валидатора",
                extra={
                    "step_name": current_step.get("name"),
                    "validator_type": validator.__class__.__name__,
                    "user_input": msg.text,
                    "error": str(e),
                    "user_id": msg.from_user.id,
                    "chat_id": msg.chat.id,
                },
            )
            await msg.reply(
                text="❗️ Произошла ошибка при обработке вашего сообщения. Попробуйте позже."
            )
            return

    user_data = step_data.get("data", {})
    groups = step_data.get("_groups")
    group_index = step_data.get("_group_index")

    current_group = groups[group_index]
    group_name = current_group.get("name")

    if group_name not in user_data:
        user_data[group_name] = {}

    user_data[group_name][current_step["name"]] = msg.text

    step_data["data"] = user_data
    step_data["_step_index"] += 1
    step_data.pop("current_step", None)
    await state.set_data(step_data)

    log.info(
        "Пользователь %s успешно прошёл шаг '%s' (text)",
        msg.from_user.id,
        current_step.get("name"),
    )

    await process_next_step(msg, state, uow)


def extract_photos(obj: Message | AlbumMessage) -> list[PhotoSize]:
    """Извлекает фотографии из сообщения"""
    if isinstance(obj, Message):
        return [obj.photo[-1]]
    elif isinstance(obj, AlbumMessage):
        return [msg.photo[-1] for msg in obj]
    else:
        raise ValueError(f"Неверный тип объекта: {type(obj)}")


async def process_media_step(
    message: Message | AlbumMessage,
    state: FSMContext,
    uow: UnitOfWork,
    media_items: list[str],
    media_key: str,
):
    """Универсальная обработка фото/видео для шага (с корректным названием)."""
    data = await state.get_data()
    steps = data.get("_steps", [])
    step_index = data.get("_step_index", 0)

    step = steps[step_index]
    step_type = step.get("type")
    step_name = step["name"]

    user_data = data.get("data", {})
    groups = data.get("_groups")
    group_index = int(data.get("_group_index"))

    current_group = groups[group_index]

    group_name = current_group.get("name")

    required_count = step.get("count")

    # Выбираем правильное название для сообщений
    if step_type == "photo":
        label = "фото"
    else:
        label = "материалы"

    media_list = user_data.get(group_name, {}).get(step_name, [])

    # Добавляем новые файлы
    for file_id in media_items:
        if required_count and len(media_list) >= required_count:
            await message.answer(
                f"Спасибо! Вы загрузили больше файлов, чем нужно. "
                f"Мы учтём только первые {required_count} — остальные не будут использованы."
            )
            await asyncio.sleep(2)
            break
        media_list.append({media_key: file_id})

    # Обновляем состояние
    user_data.setdefault(group_name, {})[step_name] = media_list
    data["data"] = user_data
    await state.set_data(data)

    log.info(
        "Пользователь %s загрузил %s (%s/%s) для шага '%s'",
        message.from_user.id,
        label,
        len(media_list),
        required_count,
        step_name,
    )

    # Проверка на завершение шага
    if required_count and len(media_list) >= required_count:
        data["_step_index"] = step_index + 1
        await state.set_data(data)
        await message.answer(f"Загружено {required_count} {label}. Переходим далее.")
        await process_next_step(message, state, uow)
    else:
        await message.answer(
            f"{label.capitalize()} {len(media_list)} из {required_count}. Отправьте ещё."
        )


@router.message(TemplateFormStates.WaitingStep, F.video, ~F.media_group_id)
async def handle_video_step(
    message: Message | AlbumMessage,
    state: FSMContext,
    uow: UnitOfWork,
):
    """Обработка видео (как материалы)."""
    if not await validate_message_for_step(message, state):
        return

    if message.video.file_size > 1024 * 1024 * 300:
        await message.reply("Видео слишком большое. Максимальный размер — 300 МБ.")
        return

    media_item = message.video.file_id

    data = await state.get_data()
    steps = data.get("_steps", [])
    step_index = data.get("_step_index", 0)

    step = steps[step_index]

    step_name = step["name"]

    user_data = data.get("data", {})
    groups = data.get("_groups")
    group_index = int(data.get("_group_index"))

    current_group = groups[group_index]

    group_name = current_group.get("name")

    user_data.setdefault(group_name, {})[step_name] = {"video_id": media_item}

    data["data"] = user_data
    data["_step_index"] = data.get("_step_index", 0) + 1

    await state.set_data(data)
    await process_next_step(message, state, uow)


@router.message(TemplateFormStates.WaitingStep, F.photo, ~F.text)
async def handle_photo_step(
    message: Message | AlbumMessage,
    state: FSMContext,
    uow: UnitOfWork,
):
    """Обработка фото."""
    if not await validate_message_for_step(message, state):
        return

    data = await state.get_data()
    current_step = data.get("current_step")

    validators = ImageValidatorFactory.create_validators(current_step.get("validators"))

    steps = data.get("_steps", [])
    step = steps[data.get("_step_index", 0)]
    step_type = step.get("type")

    if step_type in {"multi", "media"}:

        if isinstance(message, AlbumMessage):
            photos = [msg.photo[-1] for msg in message]
        else:
            photos = [message.photo[-1]]

        valid = []
        invalid = []

        for photo in photos:
            media_info = ImageInfo(
                width=photo.width,
                height=photo.height,
                size_bytes=photo.file_size,
            )
            is_valid = True
            for validator in validators:
                result = await validator.validate(media_info)

                if not result.is_valid:
                    invalid.append([photo.file_id, result.error_text])
                    is_valid = False
                    break
            if is_valid:
                valid.append(photo.file_id)

        if invalid:

            media_items = [
                InputMediaPhoto(
                    media=file_id,
                    caption=f"⚠️ {error_text}" if error_text else None,
                )
                for file_id, error_text in invalid
            ]

            await message.answer_media_group(media=media_items)

            await message.answer(
                "⚠️ Не смогли обработать фото выше. Нажмите на фото и узнайте причину ошибки."
            )

            if not valid:
                return

        await process_media_step(
            message=message,
            state=state,
            uow=uow,
            media_items=valid,
            media_key="photo_url",
        )

    else:
        for validator in validators:
            try:
                image_info = ImageInfo(
                    width=message.photo[-1].width,
                    height=message.photo[-1].height,
                    size_bytes=message.photo[-1].file_size,
                )
                result = await validator.validate(image_info)
                if not result.is_valid:
                    log.info(
                        "Валидация провалена",
                        extra={
                            "step_name": current_step.get("name"),
                            "validator_type": validator.__class__.__name__,
                            "user_input": message.photo[-1],
                            "validation_error": result.error_text,
                            "user_id": message.from_user.id,
                            "chat_id": message.chat.id,
                        },
                    )
                    if validator.error_media_id and validator.error_media_type:
                        if validator.error_media_type == "photo":
                            await message.reply_photo(
                                photo=validator.error_media_id,
                                caption=(
                                    f"⚠️ {result.error_text}"
                                    if result.error_text
                                    else None
                                ),
                            )
                        elif validator.error_media_type == "video":
                            await message.reply_video(
                                video=validator.error_media_id,
                                caption=(
                                    f"⚠️ {result.error_text}"
                                    if result.error_text
                                    else None
                                ),
                            )
                    else:
                        await message.reply(text=f"⚠️ {result.error_text}")
                    return
            except Exception as e:
                log.exception(
                    "Исключение при выполнении валидатора",
                    extra={
                        "step_name": current_step.get("name"),
                        "validator_type": validator.__class__.__name__,
                        "user_input": message.photo[-1],
                        "error": str(e),
                        "user_id": message.from_user.id,
                        "chat_id": message.chat.id,
                    },
                )
                await message.reply(
                    text="❗️ Произошла ошибка при обработке вашего сообщения. Попробуйте позже."
                )
                return
        # Обычное одно фото
        groups = data.get("_groups")
        group_index = int(data.get("_group_index"))
        current_group = groups[group_index]
        group_name = current_group.get("name")
        step_name = step["name"]

        user_data = data.get("data", {})
        user_data.setdefault(group_name, {})[step_name] = {
            "photo_url": message.photo[-1].file_id
        }

        data["data"] = user_data
        data["_step_index"] = data.get("_step_index", 0) + 1
        await state.set_data(data)

        log.info(
            "Пользователь %s загрузил фото для шага '%s'",
            message.from_user.id,
            step_name,
        )

        await asyncio.sleep(2)
        await process_next_step(message, state, uow)


# @router.callback_query(TemplateFormStates.WaitingStep)
# async def handle_select(
#     call: CallbackQuery,
#     state: FSMContext,
#     uow: UnitOfWork,
# ):
#     step_data = await state.get_data()
#     current_step = step_data.get("current_step")
#
#     if not current_step:
#         log.warning(
#             "У пользователя %s не найден current_step при callback",
#             call.from_user.id,
#         )
#         await call.answer("Ошибка. Попробуйте /start", show_alert=True)
#         await state.clear()
#         return
#
#     if current_step.get("type") != "select":
#         await validate_message_for_step(call.message, state)
#         return
#
#     value = call.data
#     options = current_step.get("options", [])
#     valid_values = [opt if isinstance(opt, str) else opt["value"] for opt in options]
#
#     if value not in valid_values:
#         log.warning(
#             "Пользователь %s сделал недопустимый выбор '%s' для шага '%s'",
#             call.from_user.id,
#             value,
#             current_step.get("name"),
#         )
#         await call.answer("Недопустимый выбор", show_alert=True)
#         return
#
#     user_data = step_data.get("data", {})
#     groups = step_data.get("_groups")
#     group_index = step_data.get("_group_index")
#
#     group_name = groups[group_index]
#
#     if group_name not in user_data:
#         user_data[group_name] = {}
#
#     user_data[group_name][current_step["name"]] = value
#
#     step_data["data"] = user_data
#     step_data["_step_index"] += 1
#     step_data.pop("current_step", None)
#     await state.set_data(step_data)
#
#     log.info(
#         "Пользователь %s выбрал '%s' для шага '%s'",
#         call.from_user.id,
#         value,
#         current_step.get("name"),
#     )
#
#     await call.answer()
#     await process_next_step(call.message, state, uow)


@router.callback_query(TemplateFormStates.Confirmed, F.data == "restart")
async def handle_restart(
    call: CallbackQuery,
    state: FSMContext,
    db_session: AsyncSession,
    uow: UnitOfWork,
):
    await call.message.delete()
    state_data = await state.get_data()

    template_id = state_data.get("template_id")
    result = await db_session.execute(
        select(TemplateORM).where(TemplateORM.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        log.error(
            "Не найден template_id=%s при рестарте для пользователя %s",
            template_id,
            call.from_user.id,
        )
        await call.message.answer("Ошибка. Шаблон не найден.")
        return

    expanded_steps = expand_steps(template.form_steps)
    await state.clear()

    await state.set_data(
        {
            "template_id": template.id,
            "_steps": expanded_steps,
            "_step_index": 0,
            "data": {},
        }
    )

    log.info(
        "Пользователь %s перезапустил заполнение шаблона %s",
        call.from_user.id,
        template.id,
    )

    await call.message.answer("Начнём оформление заказа заново.")
    await process_next_step(call.message, state, uow)


@router.callback_query(F.data.startswith("select:"))
async def handle_select_choice(
    callback: CallbackQuery, state: FSMContext, uow: UnitOfWork
):
    try:
        _, choice_value = callback.data.split(":", 1)
    except ValueError:
        await callback.answer("⚠️ Некорректный формат данных", show_alert=True)
        return

    data = await state.get_data()

    current_step = data.get("current_step", {})
    step_name = current_step.get("name")
    options = current_step.get("options", [])
    user_data = data.get("data", {})

    group_index = data.get("_group_index")
    groups = data.get("_groups", [])

    if (
        not isinstance(groups, list)
        or group_index is None
        or group_index >= len(groups)
    ):
        await callback.answer("⚠️ Ошибка состояния — группа не найдена", show_alert=True)
        return

    current_group = groups[group_index]
    group_name = current_group.get("name")
    group_data = user_data.setdefault(group_name, {})

    # Находим выбранную опцию
    selected = next((opt for opt in options if opt.get("value") == choice_value), None)

    if not selected:
        await callback.answer("⚠️ Некорректный выбор", show_alert=True)
        return

    # Сохраняем выбранную опцию по имени шага
    group_data[step_name] = selected.get("label")

    # Сохраняем action отдельно
    action = selected.get("action")
    if action:
        group_data["action"] = action

    await state.update_data({"data": user_data})

    # Подготавливаем новые шаги
    next_steps_names = selected.get("next_steps", [])
    all_steps = data.get("_all_steps", [])

    # Собираем все шаги по имени
    step_lookup = {
        s["name"]: s
        for group in all_steps
        for s in group.get("steps", [])
        if "name" in s
    }

    # Если пользователь выбрал "skip", просто пропускаем шаг
    if selected.get("action") == "skip":
        data["_step_index"] += 1
        await state.set_data(data)
        await callback.answer("Шаг пропущен ✅")
        await process_next_step(callback.message, state, uow)
        return

    # Получаем шаги для перехода
    new_steps = [step_lookup[name] for name in next_steps_names if name in step_lookup]

    # Защита: если next_steps пустой → идём к следующему шагу
    # if not new_steps:
    #     data["_step_index"] += 1
    #     await state.set_data(data)
    #     await callback.answer("Переходим к следующему шагу ✅")
    #     await process_next_step(callback.message, state, uow)
    #     return

    # Обновляем шаги FSM
    await state.update_data(
        {
            "_steps": new_steps,
            "_step_index": 0,
        }
    )

    await callback.message.answer(
        f"✅ Вы выбрали: {selected.get('label', choice_value)}"
    )
    await process_next_step(callback.message, state, uow)
