from aiogram import Router
from aiogram.types import CallbackQuery

from src.application.exceptions.supply_excptions import (
    SupplyNotFoundError,
    SupplyAlreadyClosedError,
)
from src.application.supply.use_cases.close_supply import CloseSupplyUseCase
from src.application.supply.use_cases.get_active_supply_use_case import (
    GetActiveSuppliesUseCase,
)
from src.bot.keyboards.callbacks.supply import SupplyCallback
from src.bot.keyboards.manager import supply_list_keyboard, supply_actions_keyboard
from src.database.uow import UnitOfWork

router = Router()


@router.callback_query(SupplyCallback.filter())
async def handle_supply_actions(
    call: CallbackQuery, callback_data: SupplyCallback, uow: UnitOfWork
):
    supply_id = callback_data.id
    action = callback_data.action

    try:
        if action == "select":
            supply = await uow.supply.get_by_id(supply_id)
            if not supply:
                await call.answer("❌ Поставка не найдена", show_alert=True)
                return

            supply_text = (
                f"📦 Поставка {supply.id}\n\n"
                f"  <b>- Название:</b> <code>{supply.name}</code>\n"
                f"  <b>- Количество заказов:</b> <code>{supply.order_count}</code>\n"
                f"  <b>- Дата создания:</b> <code>{supply.created_at.strftime("%d-%m-%Y %H:%M")}</code>\n"
            )

            await call.message.edit_text(
                text=supply_text,
                reply_markup=supply_actions_keyboard(supply_id, is_active=True),
            )

        elif action == "close":
            supply = await CloseSupplyUseCase(uow.supply).execute(supply_id)
            await call.answer(f"✅ Поставка {supply.name} закрыта")
            await call.message.edit_reply_markup(
                reply_markup=supply_actions_keyboard(supply_id, is_active=False)
            )

        elif action == "back":
            supplies = await GetActiveSuppliesUseCase(uow.supply).execute()
            if not supplies:
                await call.answer("⚠️ Нет активных поставок", show_alert=True)
            await call.message.edit_text(
                "📦 Выберите активную поставку:",
                reply_markup=supply_list_keyboard(supplies),
            )

    except SupplyNotFoundError:
        await call.answer("❌ Поставка не найдена", show_alert=True)
    except SupplyAlreadyClosedError:
        await call.answer("⚠️ Поставка уже закрыта", show_alert=True)
