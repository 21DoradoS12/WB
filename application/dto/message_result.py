from typing import Optional

from src.core.models.base import BaseModelWithConfig


class MessageResult(BaseModelWithConfig):
    text: str
    photo_id: Optional[str] = None
