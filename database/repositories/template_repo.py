from typing import Sequence, Optional

from sqlalchemy import select, and_

from src.database.models import TemplateORM
from src.database.repositories import BaseRepository
from src.domain.models.template import Template


class TemplateRepository(BaseRepository):
    async def get_templates_by_category(
        self,
        category_id: int,
        only_active: bool = True,
    ) -> Sequence[TemplateORM]:
        """
        Получает шаблоны по ID каталога

        :param category_id: ID каталога для выборки
        :param only_active: Только активные шаблоны (is_active=True)
        :return: Список найденных шаблонов
        """
        conditions = [TemplateORM.category_id == category_id]

        if only_active:
            conditions.append(TemplateORM.is_active.is_(True))

        result = await self.session.execute(
            select(TemplateORM).where(and_(*conditions))
        )
        return result.scalars().all()

    async def get_template_by_id(self, template_id: int) -> Optional[TemplateORM]:
        """
        Получает шаблон по идентификатору
        """
        return await self.session.get(TemplateORM, template_id)

    async def get_by_id(self, template_id) -> Optional[Template]:
        template = await self.session.get(TemplateORM, template_id)
        if not template:
            return None

        return Template.model_validate(template)
