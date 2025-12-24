from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message


class IsPrivateChat(BaseFilter):
    """
    Фильтр для проверки, является ли чат приватным.
    """

    async def __call__(self, data: Union[Message, CallbackQuery]) -> bool:
        if isinstance(data, Message):
            chat_type = data.chat.type
        elif isinstance(data, CallbackQuery) and data.message:
            chat_type = data.message.chat.type
        else:
            return False

        return chat_type == "private"
