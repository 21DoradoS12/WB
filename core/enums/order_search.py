class OrderSearchStatus:
    PENDING = "PENDING"
    """Поиск еще не завершен"""
    FOUND = "FOUND"
    """Заказ найден в базе"""
    NOT_FOUND = "NOT_FOUND"
    """Заказ не найден в базе"""
    TIMEOUT = "TIMEOUT"
    """Заказ не найден в базе (таймаут)"""
    FOUND_BUT_LINKED = "FOUND_BUT_LINKED"
    """Заказ найден в базе, но уже связан с другим заказом"""
    FOUND_IN_OTHER_WAREHOUSE = "FOUND_IN_OTHER_WAREHOUSE"
    """Заказ найден в базе, но не в нашем складе"""
    FOUND_MULTIPLE = "FOUND_MULTIPLE"
    """Найдено несколько заказов"""
    CANCELED = "CANCELED"
    """Заказ отменен"""

    @staticmethod
    def to_text(status: str) -> str:
        """
        Преобразует статус из enum в читаемый текст
        """
        status_text_mapping = {
            "PENDING": "Поиск еще не завершен",
            "FOUND": "Заказ найден в базе",
            "NOT_FOUND": "Заказ не найден в базе",
            "TIMEOUT": "Заказ не найден (таймаут)",
            "FOUND_BUT_LINKED": "Заказ найден, но уже связан с другим заказом",
            "FOUND_IN_OTHER_WAREHOUSE": "Заказ найден, но не в нашем складе",
            "FOUND_MULTIPLE": "Найдено несколько заказов",
            "CANCELED": "Заказ отменен",
        }
        return status_text_mapping.get(status, str(status))
