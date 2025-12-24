from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.bot.keyboards.user import material_keyboard

router = Router(name=__name__)


@router.message(CommandStart())
async def start_command(message: Message):
    await message.answer(
        text=(
            f"{message.from_user.first_name}, добро пожаловать в наш магазин!\n\n"
            "Чтобы отправить материал для вашего заказа, просто нажмите кнопку «Отправить материал» ниже."
        ),
        reply_markup=material_keyboard(),
    )
