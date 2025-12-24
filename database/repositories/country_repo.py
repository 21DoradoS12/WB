from typing import Sequence, Optional

from sqlalchemy import select

from src.database.models import CountryORM
from src.database.repositories import BaseRepository


class CountryRepository(BaseRepository):
    async def get_countries(self) -> Sequence[CountryORM]:
        """
        Получает список стран
        """

        result = await self.session.execute(select(CountryORM))
        return result.scalars().all()

    async def get_country_by_id(self, country_id: int) -> Optional[CountryORM]:
        """
        Получает страну по идентификатору
        """

        return await self.session.get(CountryORM, country_id)
