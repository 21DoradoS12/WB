from typing import Optional

from src.application.dto.message_result import MessageResult
from src.application.formatters.order_search.base import BaseSearchFormatter
from src.core.enums.order_search import OrderSearchStatus


class RegionSearchFormatter(BaseSearchFormatter):
    recipient_city: str
    recipient_region: str
    sender_city: str
    sender_region: str
    country: str
    order_datetime: str
    photo_id: Optional[str] = None

    def to_message(self) -> MessageResult:
        status_text = OrderSearchStatus.to_text(self.status)

        text = self.build_search_id_block()
        text += (
            f"<b>Страна:</b> {self.country}\n"
            f"<b>Город отправления:</b> <code>{self.sender_city}, {self.sender_region}</code>\n"
            f"<b>Город получателя:</b> <code>{self.recipient_city}, {self.recipient_region}</code>\n"
            f"<b>Дата заказа:</b> <code>{self.order_datetime}</code>\n"
            f"<b>Статус:</b> <code>{status_text}</code>\n"
        )
        text += self.build_end_block()
        return MessageResult(text=text, photo_id=self.photo_id)
