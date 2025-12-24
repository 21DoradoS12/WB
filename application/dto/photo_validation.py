from typing import Optional

from src.core.models.base import BaseModelWithConfig


class ImageInfo(BaseModelWithConfig):
    width: int
    height: int
    size_bytes: int
    format: Optional[str] = None
