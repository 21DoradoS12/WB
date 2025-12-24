from enum import Enum

from aiogram.filters.callback_data import CallbackData


class PaymentAction(str, Enum):
    PAY = "pay"
    NOT_PAY = "not_pay"


class PaymentCallback(CallbackData, prefix="pay"):
    action: str
    material_id: int
    stage: int | None = None
