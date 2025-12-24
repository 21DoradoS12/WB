from typing import Optional

from src.database.models import MaterialORM
from src.database.repositories import BaseRepository
from src.domain.models.material import Material


class MaterialRepository(BaseRepository):
    async def create(self, material: MaterialORM) -> MaterialORM:
        """
        Добавляет материал
        """

        self.session.add(material)
        await self.session.commit()
        return material

    async def get_by_id(self, material_id: int) -> Optional[Material]:
        material = await self.session.get(MaterialORM, material_id)

        if not material:
            return None

        return Material.model_validate(material)
