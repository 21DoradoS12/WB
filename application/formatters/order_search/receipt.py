from src.application.dto.message_result import MessageResult
from src.application.formatters.order_search.base import BaseSearchFormatter
from src.core.enums.order_search import OrderSearchStatus


class ReceiptSearchFormatter(BaseSearchFormatter):
    receipt_number: str

    def to_message(self) -> MessageResult:
        status_text = OrderSearchStatus.to_text(self.status)

        text = self.build_search_id_block()
        text += (
            f"<b>Номер чека:</b> <code>{self.receipt_number}</code>\n"
            f"<b>Статус:</b> <code>{status_text}</code>\n"
        )
        text += self.build_end_block()

        return MessageResult(text=text)
