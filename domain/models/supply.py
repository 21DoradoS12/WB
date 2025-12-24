from datetime import datetime
from enum import Enum
from typing import Optional

from src.application.exceptions.supply_excptions import SupplyAlreadyClosedError
from src.core.models.base import BaseModelWithConfig


class SupplyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Supply(BaseModelWithConfig):
    id: str
    name: str
    category_name: str
    updated_at: datetime
    created_at: datetime
    order_count: int
    status: Optional[SupplyStatus] = None

    def is_active(self) -> bool:
        """Проверяет, активна ли поставка."""
        return self.status == "active"

    def is_inactive(self) -> bool:
        """Проверяет, закрыта ли поставка."""
        return not self.is_active()

    def close(self):
        """Закрывает поставку."""
        if self.is_inactive():
            raise SupplyAlreadyClosedError()
        self.status = SupplyStatus.INACTIVE
