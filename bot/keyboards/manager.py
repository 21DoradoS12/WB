from typing import List

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.application.dto.material.material_info_dto import MaterialInfoDTO
from src.bot.keyboards.callbacks.material import MaterialActionCallback
from src.bot.keyboards.callbacks.supply import SupplyCallback
from src.domain.models.supply import Supply


def material_action_keyboard(material_info: MaterialInfoDTO) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру для действий с материалом
    """
    keyboard = InlineKeyboardBuilder()

    if not material_info.order:
        keyboard.button(
            text="Связать со сборочным",
            callback_data=MaterialActionCallback(
                action="bind_assembly",
                material_id=material_info.id,
            ),
        )

    keyboard.adjust(1)

    return keyboard.as_markup()


def supply_list_keyboard(supplies: List[Supply]) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру для выбора поставки
    """
    keyboard = InlineKeyboardBuilder()

    for supply in supplies:
        keyboard.button(
            text=supply.name,
            callback_data=SupplyCallback(id=supply.id, action="select"),
        )

    keyboard.adjust(1)
    return keyboard.as_markup()


def supply_actions_keyboard(supply_id: str, is_active: bool) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру для действий с поставкой
    """

    keyboard = InlineKeyboardBuilder()

    if is_active:
        keyboard.button(
            text="🔒 Закрыть поставку",
            callback_data=SupplyCallback(id=supply_id, action="close"),
        )

    keyboard.button(text="⬅️ Назад", callback_data=SupplyCallback(action="back"))

    keyboard.adjust(1)
    return keyboard.as_markup()
