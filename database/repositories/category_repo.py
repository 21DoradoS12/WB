from typing import Sequence, Optional

from sqlalchemy import select

from src.database.models import CategoryORM
from src.database.repositories import BaseRepository


class CategoryRepository(BaseRepository):
    async def get_active_category(self) -> Sequence[CategoryORM]:
        """
        Получает все активные категории
        """

        result = await self.session.execute(
            select(CategoryORM).where(CategoryORM.is_active.is_(True))
        )

        return result.scalars().all()

    async def get_by_id(self, category_id: int) -> Optional[CategoryORM]:
        """
        Получает категорию по идентификатору
        """

        return await self.session.get(CategoryORM, category_id)
