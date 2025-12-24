from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.application.supply.use_cases.get_active_supply_use_case import (
    GetActiveSuppliesUseCase,
)
from src.bot.keyboards.manager import supply_list_keyboard
from src.database.uow import UnitOfWork

router = Router()


@router.message(Command("supply"))
async def show_supplies(message: Message, uow: UnitOfWork):
    use_case = GetActiveSuppliesUseCase(supply_repository=uow.supply)
    supplies = await use_case.execute()

    if not supplies:
        await message.answer("❌ Нет активных поставок")
        return

    await message.answer(
        "📦 Выберите поставку:",
        reply_markup=supply_list_keyboard(supplies),
    )
