from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from src.core.config.settings import settings


class IsAdminFilter(BaseFilter):
    """
    Фильтр: проверяет, является ли пользователь администратором.
    """

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = event.from_user.id
        return user_id == settings.ADMIN_ID
