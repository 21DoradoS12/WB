from typing import Optional

from src.application.dto.wb_order.wb_assembly_task_dto import WbAssemblyTaskDTO
from src.core.models.base import BaseModelWithConfig


class WbOrderDTO(BaseModelWithConfig):
    id: str
    region_name: str
    is_cancel: bool
    assembly_task: Optional[WbAssemblyTaskDTO] = None
