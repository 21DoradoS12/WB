from datetime import datetime
from typing import Optional

from src.core.models.base import BaseModelWithConfig


class WbAssemblyTask(BaseModelWithConfig):
    id: int
    wb_order_id: str
    supply_id: Optional[str] = None
    added_to_supply_at: Optional[datetime] = None
    created_at: datetime
