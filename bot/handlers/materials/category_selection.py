from aiogram import Router, F
from aiogram.types import CallbackQuery

from src.bot.keyboards.callbacks.category import CategoryCallback
from src.bot.keyboards.user import select_template_keyboard
from src.database.uow import UnitOfWork

router = Router(name=__name__)


@router.callback_query(CategoryCallback.filter(F.action == "select"))
async def select_category(
    call: CallbackQuery,
    uow: UnitOfWork,
    callback_data: CategoryCallback,
):
    category = await uow.category.get_by_id(callback_data.id)

    templates = await uow.template.get_templates_by_category(
        category_id=callback_data.id,
        only_active=True,
    )

    if not templates:
        await call.answer(
            text="К сожалению, в данной категории нет шаблонов",
            show_alert=True,
        )
        return
    await call.message.delete()
    await call.message.answer(
        text=f"Выберите шаблон в категории {category.name}:",
        reply_markup=select_template_keyboard(templates=templates),
    )
