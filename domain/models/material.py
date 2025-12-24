from src.core.models.base import BaseModelWithConfig


class Material(BaseModelWithConfig):
    id: int
    user_id: int
    status: str
    data: dict
    template_id: int
