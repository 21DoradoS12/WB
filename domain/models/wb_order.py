from typing import Optional

from src.core.models.base import BaseModelWithConfig


class WbOrder(BaseModelWithConfig):
    id: str
    material_id: int
    region_name: str
    is_cancel: bool
    material_id: Optional[int] = None
    nm_id: int
