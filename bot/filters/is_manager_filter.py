from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from src.core.config.settings import settings


class IsManagerInChat(BaseFilter):
    async def __call__(self, data: Message | CallbackQuery) -> bool:
        """
        Пропустить пользователя, если он участник чата, где есть хотя бы один менеджер
        """
        if not isinstance(data, (Message, CallbackQuery)):
            return False

        user = data.from_user
        chat_id = settings.ADMIN_CHAT_ID

        if not user or not chat_id:
            return False

        # Получаем список участников чата, которые являются менеджерами
        try:
            member = await data.bot.get_chat_member(chat_id, user.id)
            if member.status in ("member", "administrator", "creator"):
                return True
        except Exception:
            return False

        return False
