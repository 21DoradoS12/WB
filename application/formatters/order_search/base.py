from pydantic import BaseModel

from src.application.dto.message_result import MessageResult


class BaseSearchFormatter(BaseModel):
    """
    Базовый класс для всех типов поиска заказов.
    Хранит фильтры и статус и определяет интерфейс to_message().
    """

    search_id: int
    search_type: str
    status: str

    def build_search_id_block(self) -> str:
        return (
            "🔹 <b>Информация о поисковом запросе</b> 🔹\n"
            "════════════════════════════\n"
            f"<b>Идентификатор поиска:</b> <code>{self.search_id}</code>\n"
            f"<b>Тип поиска:</b> <code>{self.search_type}</code>\n\n"
            "<b>🧾 Детали поиска</b>\n"
            "════════════════════════════\n"
        )

    def build_end_block(self) -> str:
        return "════════════════════════════"

    def to_message(self) -> MessageResult:
        raise NotImplementedError("Должен быть реализован в наследнике")
