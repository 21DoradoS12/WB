import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy import select

from src.bot.states import TemplateFormStates
from src.bot.utils.upload_materials import (
    expand_steps,
    process_next_step,
)
from src.database.models import TemplateORM
from src.database.uow import UnitOfWork

router = Router(name=__name__)
log = logging.getLogger(__name__)


@router.callback_query(TemplateFormStates.Confirmed, F.data == "confirm")
async def confirm_material(
    call: CallbackQuery,
    state: FSMContext,
    uow: UnitOfWork,
):
    await state.set_state(TemplateFormStates.WaitingStep)
    data = await state.get_data()
    data["_step_index"] += 1
    await state.set_data(data)

    confirmation_message = "✅ Отлично! Макет утверждён!\n"

    await call.message.edit_caption(caption=confirmation_message, reply_markup=None)
    await call.answer(text=confirmation_message, show_alert=True)

    await process_next_step(call.message, state, uow)


@router.callback_query(TemplateFormStates.Confirmed, F.data == "restart_template")
async def handle_restart(
    call: CallbackQuery,
    state: FSMContext,
    uow: UnitOfWork,
):
    await call.message.delete()
    state_data = await state.get_data()

    template_id = state_data.get("template_id")
    result = await uow.session.execute(
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

    await state.clear()

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

    await call.message.answer("Начнём оформление заказа заново.")

    log.info(
        "Пользователь %s начал заполнение шаблона id=%s с начала(%s шагов)",
        call.from_user.id,
        template.id,
        len(expanded_steps),
    )

    await process_next_step(call.message, state, uow)
