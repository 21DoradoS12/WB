from aiogram.filters.callback_data import CallbackData


class CityCb(CallbackData, prefix="city"):
    action: str
    city_id: int
