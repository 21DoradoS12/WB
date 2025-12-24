from aiogram.filters.callback_data import CallbackData


class MaterialActionCallback(CallbackData, prefix="material"):
    material_id: int
    action: str
