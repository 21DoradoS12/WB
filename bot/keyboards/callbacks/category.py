from typing import Optional

from aiogram.filters.callback_data import CallbackData


class CategoryCallback(CallbackData, prefix="category"):
    action: str
    id: Optional[int] = None
