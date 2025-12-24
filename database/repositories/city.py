from typing import Optional

from src.database.models import CityORM
from src.database.repositories import BaseRepository


class CityRepository(BaseRepository):
    async def get_city_by_id(self, city_id: int) -> Optional[CityORM]:
        """
        Получает город по идентификатору
        """

        return await self.session.get(CityORM, city_id)
