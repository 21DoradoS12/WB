import logging
from pathlib import Path
from typing import Optional, List

from aiogram import Bot
from aiogram.types import FSInputFile, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.notification_service.entities import NotificationMessage
from src.notification_service.entities.notification_message import Button

log = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send(self, notification: NotificationMessage) -> bool:
        try:
            keyboard = self._create_keyboard(
                notification.buttons, row_width=notification.buttons_row_width
            )

            if notification.type == "text" and notification.text:
                await self.bot.send_message(
                    chat_id=notification.chat_id,
                    text=notification.text,
                    reply_markup=keyboard,
                    message_thread_id=notification.message_thread_id,
                )

            elif (
                notification.type in {"photo", "video", "document"}
                and notification.content
            ):
                content = self._resolve_content(notification.content)

                send_kwargs = {
                    "chat_id": notification.chat_id,
                    "caption": notification.text or "",
                    "reply_markup": keyboard,
                    "message_thread_id": notification.message_thread_id,
                }

                if notification.type == "photo":
                    send_kwargs["photo"] = content
                    await self.bot.send_photo(**send_kwargs)

                elif notification.type == "video":
                    send_kwargs["video"] = content
                    await self.bot.send_video(**send_kwargs)

                elif notification.type == "document":
                    send_kwargs["document"] = content
                    await self.bot.send_document(**send_kwargs)

            else:
                log.error(
                    f"Неверный тип уведомления или отсутствуют данные: {notification}"
                )
                return False

            log.info(f"✅ Уведомление отправлено: {notification}")
            return True

        except Exception as e:
            log.error(f"❌ Ошибка отправки уведомления: {e}")
            return False

    def _resolve_content(self, content: str):
        """
        Определяет тип контента:
          - Если путь к локальному файлу → возвращает InputFile
          - Если file_id или URL → возвращает строку
        """
        path = Path(content)
        if path.exists() and path.is_file():
            return FSInputFile(path=path)  # <-- вот это ключевое изменение
        return content

    async def close(self):
        await self.bot.session.close()

    def _create_keyboard(
        self,
        buttons: Optional[List[Button]],
        row_width: int,
    ) -> Optional[InlineKeyboardMarkup]:
        if not buttons:
            return None

        keyboard = InlineKeyboardBuilder()
        for btn in buttons:
            if btn.url:
                keyboard.button(text=btn.text, url=btn.url)
            elif btn.callback_data:
                keyboard.button(text=btn.text, callback_data=btn.callback_data)
            else:
                keyboard.button(text=btn.text, callback_data=btn.text)

        keyboard.adjust(row_width)

        return keyboard.as_markup()
