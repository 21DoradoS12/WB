import logging
from typing import Optional

from src.notification_service.entities import NotificationMessage
from src.notification_service.services.telegram_notifier import TelegramNotifier

log = logging.getLogger(__name__)


class ForwardVideoToAdminUseCase:
    def __init__(
        self,
        notifier: TelegramNotifier,
        admin_chat_id: int,
    ):
        self.notifier = notifier
        self.admin_chat_id = admin_chat_id

    async def execute(
        self, order_id: int, file_id: str, message_thread_id: Optional[int] = None
    ):
        """
        Пересылает видео администратору с номером заказа.
        """
        try:
            log.info(
                f"📨 Пересылаю видео {file_id} для заказа {order_id} администратору"
            )

            notification = NotificationMessage(
                chat_id=self.admin_chat_id,
                type="video",
                content=file_id,
                text=f"Видео для заказа #{order_id}",
                message_thread_id=message_thread_id,
            )

            success = await self.notifier.send(notification)

            if success:
                log.info(
                    f"✅ Видео для заказа {order_id} успешно отправлено администратору"
                )
            else:
                log.error(f"❌ Не удалось отправить видео для заказа {order_id}")

        except Exception as e:
            log.error(
                f"❌ Ошибка при пересылке видео для заказа {order_id}: {e}",
                exc_info=True,
            )
