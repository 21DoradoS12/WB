from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards.callbacks.category import CategoryCallback
from src.bot.keyboards.user import select_category_keyboard
from src.database.uow import UnitOfWork

router = Router(name=__name__)


@router.callback_query(CategoryCallback.filter(F.action == "back_to_categories"))
@router.callback_query(F.data == "send_material")
async def start_send_material(call: CallbackQuery, uow: UnitOfWork):
    categories = await uow.category.get_active_category()

    if not categories:
        await call.message.edit_text(
            text="В данный момент нет активных категорий для отправки материала",
        )
        return

    await call.message.edit_text(
        text="Выберите категорию для отправки материала",
        reply_markup=select_category_keyboard(categories=categories),
    )


@router.message(Command("new_order"))
async def start_send_material(message: Message, uow: UnitOfWork):
    categories = await uow.category.get_active_category()

    if not categories:
        await message.answer(
            text="В данный момент нет активных категорий для отправки материала",
        )
        return

    await message.answer(
        text="Выберите категорию для отправки материала",
        reply_markup=select_category_keyboard(categories=categories),
    )
