from typing import Literal, Dict, Any, Optional

from pydantic import BaseModel


class GenerateTask(BaseModel):
    type: Literal["png", "psd", "pdf"]
    order_data: Dict[str, Any]
    template_id: int
    delivery: dict
    filename: Optional[str] = None
    dpi: int = 500
