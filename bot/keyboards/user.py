from typing import List

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.keyboards.callbacks.category import CategoryCallback
from src.bot.keyboards.callbacks.city import CityCb
from src.bot.keyboards.callbacks.country import CountryCallback
from src.bot.keyboards.callbacks.link_material_order import LinkMaterialToOrderCallback
from src.bot.keyboards.callbacks.payment import PaymentCallback, PaymentAction
from src.bot.keyboards.callbacks.template import TemplateCallback
from src.database.models import CategoryORM, TemplateORM, CountryORM


def material_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для отправки материала пользователем
    """
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📎 Отправить материал", callback_data="send_material")
    return keyboard.as_markup()


def select_category_keyboard(categories: List[CategoryORM]) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора категории
    """
    keyboard = InlineKeyboardBuilder()

    for category in categories:
        keyboard.button(
            text=category.name,
            callback_data=CategoryCallback(
                action="select",
                id=category.id,
            ),
        )

    keyboard.adjust(1)

    return keyboard.as_markup()


def select_template_keyboard(templates: List[TemplateORM]) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора шаблона
    """
    keyboard = InlineKeyboardBuilder()

    for template in templates:
        if template.photo:
            action = "select"
        else:
            action = "choose"
        keyboard.button(
            text=template.name,
            callback_data=TemplateCallback(
                action=action,
                id=template.id,
            ),
        )

    keyboard.button(
        text="⬅️ Вернуться к категориям",
        callback_data=CategoryCallback(action="back_to_categories"),
    )

    keyboard.adjust(1)

    return keyboard.as_markup()


def generate_select_option_keyboard(options: list):
    kb = InlineKeyboardBuilder()
    for opt in options:
        kb.button(text=opt["label"], callback_data=f"select:{opt['value']}")
    kb.adjust(1)
    return kb.as_markup()


def get_order_already_done_keyboard(material_id: int) -> InlineKeyboardMarkup:
    """
    Возвращает InlineKeyboard с кнопкой 'МОЙ ЗАКАЗ УЖЕ ОФОРМЛЕН'
    """

    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="МОЙ ЗАКАЗ УЖЕ ОФОРМЛЕН",
        callback_data=LinkMaterialToOrderCallback(material_id=material_id),
    )
    keyboard.adjust(1)
    return keyboard.as_markup()


def generate_country_kb(countries: list[CountryORM]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for country in countries:
        kb.button(
            text=country.name,
            callback_data=CountryCallback(action="select", id=country.id),
        )

    kb.adjust(1)
    return kb.as_markup()


def generate_payment_status_keyboard(
    material_id: int, show_not_paid: bool = False, stage: int = None
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="Оплатил",
        callback_data=PaymentCallback(
            action=PaymentAction.PAY, material_id=material_id, stage=stage
        ),
    )

    if show_not_paid:
        keyboard.button(
            text="Не оплатил",
            callback_data=PaymentCallback(
                action=PaymentAction.NOT_PAY, material_id=material_id, stage=stage
            ),
        )

    keyboard.adjust(1)
    return keyboard.as_markup()


def get_city_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Выбрать город", switch_inline_query_current_chat="")
    kb.adjust(1)
    return kb.as_markup()


def get_city_select_kb(city_id: int):
    """Возвращает кнопку для подтверждения выбора города. Или для выбора другого города."""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="Подтвердить выбор",
        callback_data=CityCb(action="select", city_id=city_id),
    )
    keyboard.button(text="Выбрать другой город", switch_inline_query_current_chat="")
    keyboard.adjust(1)
    return keyboard.as_markup()


def get_support_button_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Техподдержка", url="https://t.me/prizma_trek")
    keyboard.adjust(1)
    return keyboard.as_markup()
