from typing import Optional

from aiogram.filters.callback_data import CallbackData


class TemplateCallback(CallbackData, prefix="template"):
    action: str
    id: Optional[int] = None
