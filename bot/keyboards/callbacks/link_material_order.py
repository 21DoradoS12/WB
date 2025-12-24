from aiogram.filters.callback_data import CallbackData


class LinkMaterialToOrderCallback(CallbackData, prefix="link_material_order"):
    material_id: int
