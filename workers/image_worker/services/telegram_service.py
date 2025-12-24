from aiogram import Bot
from aiogram.types import BufferedInputFile


async def send_to_telegram(
    bot: Bot,
    chat_id: int,
    file_bytes: bytes,
    filename: str,
    text: str = None,
    as_photo: bool = False,
    reply_markup=None,
):
    file = BufferedInputFile(file=file_bytes, filename=filename)

    if as_photo:
        await bot.send_photo(
            caption=text, chat_id=chat_id, photo=file, reply_markup=reply_markup
        )
    else:
        await bot.send_document(
            caption=text, chat_id=chat_id, document=file, reply_markup=reply_markup
        )

    await bot.session.close()
