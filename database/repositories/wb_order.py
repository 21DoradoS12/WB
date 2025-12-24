from typing import Optional

from sqlalchemy import select

from src.database.models import WbOrderORM
from src.database.repositories import BaseRepository
from src.domain.models.wb_order import WbOrder


class WbOrderRepository(BaseRepository):
    async def get_order_by_material_id(self, material_id: int) -> Optional[WbOrderORM]:
        """
        Получает WB заказ по идентификатору материала
        """

        return await self.session.scalar(
            select(WbOrderORM).where(WbOrderORM.material_id == material_id)
        )

    async def get_by_material_id(self, material_id: int) -> Optional[WbOrder]:
        query = select(WbOrderORM).where(WbOrderORM.material_id == material_id)
        res = await self.session.execute(query)

        wb_order = res.scalar()

        if not wb_order:
            return None

        return WbOrder.model_validate(wb_order)

    async def get_by_id(self, wb_order_id: str) -> Optional[WbOrder]:
        wb_order = await self.session.get(WbOrderORM, wb_order_id)

        if not wb_order:
            return None

        return WbOrder.model_validate(wb_order)

    async def update(self, wb_order: WbOrder) -> WbOrder:

        orm_order = await self.session.get(WbOrderORM, wb_order.id)
        if not orm_order:
            orm_order = WbOrderORM(id=wb_order.id)

        orm_order.material_id = wb_order.material_id
        self.session.add(orm_order)
        await self.session.commit()

        return WbOrder.model_validate(orm_order)
