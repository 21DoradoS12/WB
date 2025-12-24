from typing import Optional

from sqlalchemy import select

from src.database.models import CategorySettingsORM
from src.database.repositories import BaseRepository


class CategorySettingsRepository(BaseRepository):
    async def get_by_category_id(
        self, category_id: int
    ) -> Optional[CategorySettingsORM]:
        query = select(CategorySettingsORM).where(
            CategorySettingsORM.category_id == category_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
