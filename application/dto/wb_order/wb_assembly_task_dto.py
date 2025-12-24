from typing import Optional

from src.application.dto.wb_order.supply import SupplyDTO
from src.core.models.base import BaseModelWithConfig


class WbAssemblyTaskDTO(BaseModelWithConfig):
    id: int
    supply: Optional[SupplyDTO] = None
