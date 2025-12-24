import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.keyboards.callbacks.category import CategoryCallback
from src.bot.keyboards.callbacks.template import TemplateCallback
from src.bot.utils.upload_materials import expand_steps, process_next_step
from src.database.uow import UnitOfWork

router = Router(name=__name__)
log = logging.getLogger(__name__)


@router.callback_query(TemplateCallback.filter(F.action == "select"))
async def select_category(
    call: CallbackQuery,
    uow: UnitOfWork,
    callback_data: TemplateCallback,
    state: FSMContext,
):
    template = await uow.template.get_template_by_id(callback_data.id)

    if not template:
        log.warning(
            "Пользователь %s выбрал несуществующий шаблон id=%s",
            call.from_user.id,
            callback_data.id,
        )
        await call.answer(text="⚠️ Данный шаблон не найден", show_alert=True)
        return

    kb = InlineKeyboardBuilder()
    kb.button(
        text="Выбрать", callback_data=TemplateCallback(id=template.id, action="choose")
    )
    kb.button(
        text="⬅️ Назад к выборку",
        callback_data=CategoryCallback(id=template.category_id, action="select"),
    )
    kb.adjust(1)

    if template.photo:
        await call.message.edit_media(
            media=InputMediaPhoto(media=template.photo, caption=template.description),
            reply_markup=kb.as_markup(),
        )
        return
    else:
        await call.message.edit_text(
            text=template.description, reply_markup=kb.as_markup()
        )


@router.callback_query(TemplateCallback.filter(F.action == "choose"))
async def select_category(
    call: CallbackQuery,
    uow: UnitOfWork,
    callback_data: TemplateCallback,
    state: FSMContext,
):
    try:
        template = await uow.template.get_template_by_id(callback_data.id)

        if not template:
            log.warning(
                "Пользователь %s выбрал несуществующий шаблон id=%s",
                call.from_user.id,
                callback_data.id,
            )
            await call.answer(text="⚠️ Данный шаблон не найден", show_alert=True)
            return

        expanded_steps = expand_steps(template.form_steps[0].get("steps"))
        groups = [i for i in template.form_steps]

        user_data = {}

        current_group = groups[0]
        group_name = current_group.get("name")
        group_action = current_group.get("action")
        group_data = user_data.setdefault(group_name, {})

        if group_action:
            group_data["action"] = group_action

        await state.set_data(
            {
                "template_id": template.id,
                "_all_steps": template.form_steps,
                "_steps": expanded_steps,
                "_step_index": 0,
                "_groups": groups,
                "_group_index": 0,
                "data": user_data,
            }
        )

        log.info(
            "Пользователь %s начал заполнение шаблона id=%s (%s шагов)",
            call.from_user.id,
            template.id,
            len(expanded_steps),
        )

        await call.message.delete()
        await process_next_step(call.message, state, uow)

    except Exception as e:
        log.exception(
            "Ошибка при выборе шаблона пользователем %s (id=%s)",
            call.from_user.id,
            callback_data.id,
        )
        await call.answer(
            text="❗️ Произошла ошибка. Попробуйте ещё раз позже.",
            show_alert=True,
        )
