import logging

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from src.application.formatters.order_search.factory import build_search_message
from src.database.uow import UnitOfWork

router = Router()
log = logging.getLogger(__name__)


@router.message(Command("order_search"))
async def order_search_handler(
    message: Message,
    command: CommandObject,
    uow: UnitOfWork,
):
    user_id = message.from_user.id if message.from_user else "unknown"
    log.debug(
        f"Получена команда /order_search от пользователя {user_id}: {command.text}"
    )

    if not command.args or len(command.args.split()) != 1:
        log.warning(f"Неверная команда от пользователя {user_id}: {command.text}")
        await message.reply(f"Укажите номер поиска.\nПример: /order_search 12345")
        return

    try:
        order_number = int(command.args.strip())
    except ValueError:
        log.warning(f"Некорректный номер заказа от пользователя {user_id}.")
        await message.reply(
            "Номер заказа должен быть числом. Попробуйте еще раз.\nПример: /order_search 12345"
        )
        return

    log.info(
        f"Начало поиска заказа с номером {order_number} для пользователя {user_id}."
    )

    try:
        order = await uow.order_search.get_by_id(order_number)

        if not order:
            log.info(
                f"Заказ с номером {order_number} не найден для пользователя {user_id}."
            )
            await message.reply(f"Поисковый запрос с номером {order_number} не найден.")
            return

        message_obj = build_search_message(
            search_type=order.search_type,
            filters=order.filters,
            status=order.status,
            search_id=order.id,
        )

        log.info(
            f"Поиск заказа с номером {order_number} завершён для пользователя {user_id}."
        )

        if message_obj.photo_id:
            await message.reply_photo(
                photo=message_obj.photo_id, caption=message_obj.text
            )
        else:
            await message.reply(message_obj.text)

    except Exception as e:
        log.error(
            f"Ошибка при обработке поиска заказа у пользователя %s с номером %s: %s",
            user_id,
            order_number,
            e,
        )
        await message.answer(
            "Произошла ошибка при обработке запроса. Попробуйте снова позже."
        )
