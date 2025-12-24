from typing import Optional

from aiogram.filters.callback_data import CallbackData


class CountryCallback(CallbackData, prefix="country"):
    action: str
    id: Optional[int] = None
