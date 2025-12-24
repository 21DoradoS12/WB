import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config.settings import settings
from src.core.database.async_session import AsyncSessionLocal
from src.core.setup_logging import setup_logging
from src.database.models import WbAssemblyTaskORM, WbOrderORM
from src.workers.wb_data.wb_api.client import WildberriesApi

log = logging.getLogger(__name__)


async def upsert_assembly_task_data_in_batches(
    session: AsyncSession, assembly_task_data: list, batch_size: int = 1000
):
    for i in range(0, len(assembly_task_data), batch_size):
        batch = assembly_task_data[i : i + batch_size]
        stmt = pg_insert(WbAssemblyTaskORM).values(batch)
        stmt = stmt.on_conflict_do_nothing()
        await session.execute(stmt)
        await session.commit()


async def upsert_orders_in_batches(
    session: AsyncSession, orders_data: list, batch_size: int = 1000
):
    for i in range(0, len(orders_data), batch_size):
        batch = orders_data[i : i + batch_size]
        stmt = pg_insert(WbOrderORM).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=[WbOrderORM.id],
            set_={
                WbOrderORM.is_cancel: stmt.excluded.is_cancel,
                WbOrderORM.cancel_date: stmt.excluded.cancel_date,
                WbOrderORM.warehouse_name: stmt.excluded.warehouse_name,
                WbOrderORM.warehouse_type: stmt.excluded.warehouse_type,
            },
        )

        # Выполняем запрос
        await session.execute(stmt)
        await session.commit()


city_to_region = {
    "Москва": "Московская область",
    "Санкт-Петербург": "Ленинградская область",
    "Севастополь": "Республика Крым",
}


async def get_wb_data_and_save_to_db():
    async with AsyncSessionLocal() as session:
        try:
            wb_api = WildberriesApi(token=settings.WB_TOKEN)
            date_from = (datetime.now() - timedelta(days=30)).date()
            wb_orders = wb_api.fetch_orders_report(date_from=str(date_from))

            # Заменяем названия городов на регионы
            for order in wb_orders.orders:
                if order.region_name in city_to_region:
                    order.region_name = city_to_region[order.region_name]

            wb_orders = [order.model_dump() for order in wb_orders.orders]
            await upsert_orders_in_batches(session, wb_orders)

            wb_order_ids = {assembly_task.get("id") for assembly_task in wb_orders}

            wb_assembly_tasks = wb_api.fetch_new_assembly_tasks()
            wb_assembly_tasks = [
                order.model_dump() for order in wb_assembly_tasks.orders
            ]

            wb_assembly_tasks = [
                task
                for task in wb_assembly_tasks
                if task.get("wb_order_id") in wb_order_ids
            ]

            await upsert_assembly_task_data_in_batches(session, wb_assembly_tasks)
            log.info(f"Данные успешно сохранены в базу данных")
        except Exception as e:
            log.error(e)
            raise


async def run_script():
    while True:
        log.info("Запускаю получение данных из WB и сохранение в базу данных")
        await get_wb_data_and_save_to_db()
        log.info("Завершено получение данных из WB и сохранение в базу данных")
        await asyncio.sleep(300)


if __name__ == "__main__":
    setup_logging(service_name="wb_data")
    try:
        asyncio.run(run_script())
    except KeyboardInterrupt as e:
        log.info("Прерывание работы программы пользователем.")
    except Exception as e:
        log.error(e, exc_info=True)
    finally:
        log.info("Завершение работы программы.")
