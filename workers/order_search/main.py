import asyncio
import logging
from datetime import timedelta, datetime, timezone
from typing import Optional

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.config.settings import settings
from src.core.database.async_session import AsyncSessionLocal
from src.core.enums.order_search import OrderSearchStatus
from src.core.setup_logging import setup_logging
from src.core.utils.time import now_utc
from src.database.models import (
    OrderSearchORM,
    WbOrderORM,
    MaterialORM,
    WbAssemblyTaskORM,
    UserORM,
    CategoryORM,
    TemplateORM,
)
from src.database.models.wb_article import WbArticleORM
from src.infrastructure.rabbitmq.producer import send_to_queue

log = logging.getLogger(__name__)

bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode="HTML",
    ),
)


async def send_message_to_admin(text):
    try:
        await bot.send_message(
            text=text,
            chat_id=settings.ADMIN_CHAT_ID,
            message_thread_id=settings.WB_NOTIFICATION_THREAD,
        )
    except Exception as e:
        log.error(f"Ошибка при отправке сообщения администратору: {e}", exc_info=True)


async def send_message_to_user(chat_id, text, keyboard=None):
    try:
        await bot.send_message(
            text=text,
            chat_id=chat_id,
            reply_markup=keyboard,
        )
    except Exception as e:
        log.error(f"Ошибка при отправке сообщения пользователю: {e}", exc_info=True)


async def get_active_search_requests(
    session: AsyncSession,
    limit: int = 100,
    offset: int = 0,
    hours_after_creation: Optional[int] = None,
):
    """
    Получить активные запросы на поиск

    limit - лимит на количество запросов
    offset - смещение от начала
    """
    query = select(OrderSearchORM).where(
        OrderSearchORM.status == OrderSearchStatus.PENDING
    )

    if hours_after_creation is not None:
        # Используем UTC время для сравнения
        target_time = datetime.now(timezone.utc) - timedelta(hours=hours_after_creation)
        query = query.where(OrderSearchORM.created_at <= target_time)

    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)

    result = await session.execute(query)

    return result.scalars().all()


async def get_region_filter(region_name: str):
    """Создание фильтра по региону с учетом особого случая для Москвы."""
    if region_name == "Московская область":
        return or_(
            WbOrderORM.region_name.ilike(f"%{region_name}%"),
            WbOrderORM.region_name.ilike("%Москва%"),
        )
    return WbOrderORM.region_name.ilike(f"%{region_name}%")


def parse_datetime_with_offset(datetime_str: str) -> datetime:
    return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S") + timedelta(hours=3)


async def get_time_filter(date_obj: datetime):
    """Создание временного фильтра в зависимости от разницы во времени."""
    return WbOrderORM.created_at.between(
        date_obj - timedelta(seconds=60), date_obj + timedelta(seconds=60)
    )


async def find_wb_orders_by_with_filters(
    session: AsyncSession, order_search: OrderSearchORM, template_id: int
) -> list[WbOrderORM]:

    try:
        search_data = order_search.filters
        search_type = order_search.search_type

        subquery = (
            select(WbArticleORM.wb_article)
            .where(WbArticleORM.template_id == template_id)
            .scalar_subquery()
        )

        if search_type != "RECEIPT_NUMBER":
            # Подготовка временных параметров
            date_obj = parse_datetime_with_offset(search_data.get("order_datetime"))

            # Базовые условия фильтрации
            base_filters = [
                WbOrderORM.is_cancel == False,
                WbOrderORM.nm_id.in_(subquery),  # Используем подзапрос здесь
                await get_time_filter(date_obj),
            ]

        # Добавление специфичных фильтров в зависимости от типа поиска
        if search_type == "COUNTRY":
            country_filter = WbOrderORM.country_name.ilike(search_data.get("country"))
            filters = [country_filter] + base_filters

        elif search_type == "REGION":
            recipient_region = search_data.get("recipient_region")

            if "республика" in recipient_region:
                recipient_region = recipient_region.replace("республика", "").strip()

            region_filter = await get_region_filter(recipient_region)
            filters = [region_filter] + base_filters
        elif search_type == "RECEIPT_NUMBER":
            receipt_number = search_data.get("receipt_number")

            filters = [WbOrderORM.id == receipt_number, WbOrderORM.nm_id.in_(subquery)]
        else:
            raise ValueError(f"Unknown search type: {search_type}")

        # Выполнение запроса
        query = select(WbOrderORM).filter(*filters)
        query = query.options(selectinload(WbOrderORM.assembly_task))

        result = await session.execute(query)
        return result.scalars().all()

    except (ValueError, KeyError) as e:
        log.error(f"Ошибка при поиске заказа: {e}", exc_info=True)
        return None


def is_search_time_expired(order_search: OrderSearchORM) -> bool:
    """Проверяет, истекло ли время поиска заказа."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    elapsed = now - order_search.created_at
    return elapsed.total_seconds() > 60 * 60 * 4


def get_username_display(username: str | None) -> str:
    """
    Возвращает отформатированное имя пользователя для отображения в сообщении.
    """
    return f"@{username}" if username else "Отсутствует"


def get_user_id_display(user_id: int) -> str:
    """
    Возвращает отформатированное ID пользователя для отображения в сообщении.
    """
    return f"<a href='tg://user?id={user_id}'>{user_id}</a>"


async def process_active_requests():
    limit = 100
    offset = 0

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Менеджер", url="https://t.me/giftoboom")

    while True:
        async with AsyncSessionLocal() as session:
            order_searches = await get_active_search_requests(
                session=session, limit=limit, offset=offset
            )

            if not order_searches:
                return

            for order_search in order_searches:

                order_search.last_checked_at = now_utc()
                await session.commit()

                res = await session.execute(
                    select(MaterialORM).where(
                        MaterialORM.id == order_search.material_id
                    )
                )
                material = res.scalar()

                res = await session.execute(
                    select(UserORM).where(UserORM.id == material.user_id)
                )
                user = res.scalar()

                wb_orders = await find_wb_orders_by_with_filters(
                    session, order_search, material.template_id
                )

                if is_search_time_expired(order_search):
                    order_search.status = OrderSearchStatus.TIMEOUT

                    user_text = (
                        f"⌛️ <b>Поиск вашего заказа завершен неудачно</b>\n"
                        "Свяжитесь с менеджером в ближайшее время, мы примем ваш заказ вручную.\n"
                    )
                    admin_message = (
                        "🚫 Завершение по времени\n\n"
                        f"👤 Пользователь:\n"
                        f"ID: {get_user_id_display(user.id)}\n"
                        f"Имя: {user.first_name}\n"
                        f"Username: {get_username_display(user.username)}\n\n"
                        f"Данные поиска:\n"
                        f"Тип поиска: {order_search.search_type}\n"
                        f"Фильтры: {order_search.filters}\n\n"
                        f"Идентификатор поиска: {order_search.id}\n\n"
                        f"Идентификатор материала: {order_search.material_id}"
                    )
                    await send_message_to_user(
                        text=user_text, chat_id=user.id, keyboard=keyboard.as_markup()
                    )
                    await send_message_to_admin(text=admin_message)
                    await session.commit()
                    continue

                if not wb_orders:
                    continue

                if len(wb_orders) > 1:
                    admin_text = (
                        f"🚫 Было найдено {len(wb_orders)} заказов"
                        f"Заявка №{order_search.id}:\n\n"
                        f"<b>👤 Пользователь:</b>\n"
                        f"ID: {get_user_id_display(user.id)}\n"
                        f"Имя: {user.first_name}\n"
                        f"Username: {get_username_display(user.username)}\n\n"
                        f"Заказы:\n {'\n'.join(i.id for i in wb_orders)}"
                    )
                    order_search.status = OrderSearchStatus.FOUND_MULTIPLE

                    user_text = (
                        f"⌛️ <b>Поиск вашего заказа завершен неудачно</b>\n"
                        "Свяжитесь с менеджером в ближайшее время, мы примем ваш заказ вручную.\n"
                    )
                    await send_message_to_user(
                        text=user_text, chat_id=user.id, keyboard=keyboard.as_markup()
                    )
                    await send_message_to_admin(admin_text)
                    await session.commit()
                    continue

                wb_order = wb_orders[0]

                res = await session.execute(
                    select(WbAssemblyTaskORM).where(
                        WbAssemblyTaskORM.wb_order_id == wb_order.id
                    )
                )

                assembly_task = res.scalar()

                template = await session.scalar(
                    select(TemplateORM).where(TemplateORM.id == material.template_id)
                )

                category = await session.scalar(
                    select(CategoryORM).where(CategoryORM.id == template.category_id)
                )

                if not assembly_task:
                    continue

                if wb_order.material_id:
                    order_search.status = OrderSearchStatus.FOUND_BUT_LINKED
                    admin_reason = "🚫 Заказ уже связан с другим материалом"
                    user_text = (
                        "ℹ️ <b>Ваш заказ уже был связан с другим</b>\n\n"
                        "Свяжитесь с менеджером в ближайшее время для уточнения деталей.\n\n"
                        f"Номер вашей заявки: #{order_search.id}"
                    )

                elif wb_order.warehouse_type == "Склад WB":
                    order_search.status = OrderSearchStatus.FOUND_IN_OTHER_WAREHOUSE
                    admin_reason = "🚫 Заказ не из нашего склада"
                    user_text = (
                        f"⌛️ <b>Поиск вашего заказа завершен неудачно</b>\n"
                        "Свяжитесь с менеджером в ближайшее время, мы примем ваш заказ вручную.\n"
                    )
                elif wb_order.is_cancel:
                    order_search.status = OrderSearchStatus.CANCELED
                    admin_reason = "🚫 Заказ был отменен"
                    user_text = (
                        f"⌛️ <b>Поиск вашего заказа завершен неудачно</b>\n"
                        "Свяжитесь с менеджером в ближайшее время для уточнения деталей.\n"
                    )
                else:
                    order_search.status = OrderSearchStatus.FOUND
                    wb_order.material_id = order_search.material_id
                    admin_reason = "✅ Заказ был найден"
                    user_text = (
                        "✅ Ваш заказ был успешно найден и отправлен в производство, ожидайте отправку.\n"
                        f"Номер вашего заказа: #{assembly_task.id}"
                    )

                admin_message = (
                    f"{admin_reason}:\n\n"
                    f"<b>👤 Пользователь:</b>\n"
                    f"ID: {get_user_id_display(user.id)}\n"
                    f"Имя: {user.first_name}\n"
                    f"Username: {get_username_display(user.username)}\n\n"
                    f"<b>📦 Детали заказа Wildberries:</b>\n"
                    f"WB ID: {wb_order.id}\n"
                    f"Сборочное задание: {assembly_task.id}\n"
                    f"Регион: {wb_order.region_name}\n"
                    f"Артикул: {wb_order.supplier_article}\n"
                    f"Дата оформления: {wb_order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    f"Идентификатор материала: {order_search.material_id}"
                )

                folder_name = category.folder_name or "unsorted"

                await send_message_to_admin(text=admin_message)
                await send_message_to_user(
                    text=user_text, chat_id=user.id, keyboard=keyboard.as_markup()
                )
                await session.commit()
                await send_to_queue(
                    queue_name="processing_supply",
                    data={
                        "assembly_task_id": assembly_task.id,
                    },
                )

            offset += limit


async def main():
    setup_logging(service_name="order_search")

    while True:
        await process_active_requests()
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
