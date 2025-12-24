from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.bot.states.admin import AdminStates

router = Router()


@router.message(Command("check_file_id"))
async def cmd_check_file_id(message: Message, state: FSMContext):
    """
    Команда /check_file_id — запускает процесс получения file_id файла.
    """
    await state.set_state(AdminStates.waiting_for_file_to_get_id)
    await message.answer("Отправьте файл что бы узнать id")


@router.message(AdminStates.waiting_for_file_to_get_id)
async def process_any_file(message: Message, state: FSMContext):
    """
    Обрабатывает любой файл и возвращает его file_id.
    """
    if message.photo:
        await message.reply(
            text=f"<b>Идентификатор фотографии:</b> <code>{message.photo[-1].file_id}</code>"
        )

    if message.video:
        await message.reply(
            text=f"<b>Идентификатор видео:</b> <code>{message.video.file_id}</code>"
        )
