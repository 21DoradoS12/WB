from typing import Optional

from aiogram.filters.callback_data import CallbackData


class SupplyCallback(CallbackData, prefix="supply"):
    action: str
    id: Optional[str] = None
