from typing import Optional

from sqlalchemy import select

from src.core.enums.order_search import OrderSearchStatus
from src.database.models import OrderSearchORM
from src.database.repositories import BaseRepository


class OrderSearchRepository(BaseRepository):

    async def get_active_search_by_material_id(
        self,
        material_id: int,
    ) -> Optional[OrderSearchORM]:
        """
        Получает активные поиски по идентификатору материала
        """

        return await self.session.scalar(
            select(OrderSearchORM).where(
                OrderSearchORM.material_id == material_id,
                OrderSearchORM.status.in_([OrderSearchStatus.PENDING]),
            )
        )

    async def get_by_id(self, order_search_id: int) -> Optional[OrderSearchORM]:
        return await self.session.get(OrderSearchORM, order_search_id)

    async def create_order_search(
        self,
        order_search: OrderSearchORM,
    ) -> OrderSearchORM:
        """
        Добавляет поисковый запрос
        """

        self.session.add(order_search)
        await self.session.commit()
        return order_search
