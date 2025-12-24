from typing import Optional, List

from sqlalchemy import select

from src.application.exceptions.supply_excptions import SupplyNotFoundError
from src.database.models import SupplyORM
from src.database.repositories import BaseRepository
from src.domain.models.supply import Supply


class SupplyRepository(BaseRepository):
    async def get_by_id(self, supply_id: str) -> Optional[Supply]:
        """Получает поставку по id"""
        supply = await self.session.get(SupplyORM, supply_id)

        if not supply:
            return None

        return Supply.model_validate(supply)

    async def get_active_supplies(self) -> List[Supply]:
        """Получает список активных поставок"""
        stmt = select(SupplyORM).where(SupplyORM.status == "active")
        result = await self.session.scalars(stmt)
        supplies_orm = result.all()

        return [Supply.model_validate(s) for s in supplies_orm]

    async def update(self, supply: Supply) -> None:
        """Обновляет существующую поставку в базе"""
        supply_orm = await self.session.get(SupplyORM, supply.id)

        if not supply_orm:
            raise SupplyNotFoundError()

        supply_orm.name = supply.name
        supply_orm.category_name = supply.category_name
        supply_orm.status = supply.status
        supply_orm.order_count = supply.order_count
