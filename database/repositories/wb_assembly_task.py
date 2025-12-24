from typing import Optional

from sqlalchemy import select

from src.database.models import WbAssemblyTaskORM
from src.database.repositories import BaseRepository
from src.domain.models.wb_assembly_task import WbAssemblyTask


class WbAssemblyTaskRepository(BaseRepository):
    async def get_by_id(self, assembly_task_id: int) -> Optional[WbAssemblyTask]:
        """
        Получить сборочное задание по уникальному идентификатору
        """
        assembly_task = await self.session.get(WbAssemblyTaskORM, assembly_task_id)

        if not assembly_task:
            return None

        return WbAssemblyTask.model_validate(assembly_task)

    async def get_by_wb_order_id(self, wb_order_id: str) -> Optional[WbAssemblyTask]:
        """
        Получить сборочное задание по wb_order_id
        """
        query = select(WbAssemblyTaskORM).where(
            WbAssemblyTaskORM.wb_order_id == wb_order_id
        )

        result = await self.session.execute(query)

        assembly_task = result.scalar()

        if not assembly_task:
            return None

        return WbAssemblyTask.model_validate(assembly_task)
