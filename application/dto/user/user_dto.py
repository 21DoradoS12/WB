from typing import Optional

from src.core.models.base import BaseModelWithConfig


class UserDTO(BaseModelWithConfig):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
