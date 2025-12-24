from typing import Optional

from src.application.dto.template_dto import TemplateDTO
from src.application.dto.user.user_dto import UserDTO
from src.application.dto.wb_order.wb_order_dto import WbOrderDTO
from src.core.models.base import BaseModelWithConfig


class MaterialInfoDTO(BaseModelWithConfig):
    id: int
    status: str
    data: dict
    user: Optional[UserDTO] = None
    order: Optional[WbOrderDTO] = None
    template: Optional[TemplateDTO] = None
