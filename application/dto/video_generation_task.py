from typing import List

from pydantic import Field

from src.core.models.base import BaseModelWithConfig


class VideoGenerationTask(BaseModelWithConfig):
    order_id: int = Field(..., description="Идентификатор заказа")
    files: List[str] = Field(..., description="Список ID файлов для обработки")
    output_path: str = Field(..., description="Путь для сохранения результата")
