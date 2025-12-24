from typing import Optional

from pydantic import Field

from src.core.models.base import BaseModelWithConfig


class GenerateVideoResult(BaseModelWithConfig):
    success: bool = Field(..., description="Флаг успешности операции")
    message: str = Field(..., description="Сообщение об операции")
    video_path: Optional[str] = Field(
        default=None,
        description="Путь к сгенерированному видео",
    )
