from pydantic import ConfigDict

from src.core.models.base import BaseModelWithConfig


class TemplateDTO(BaseModelWithConfig):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
