from sqlalchemy import select

from src.database.models import WbArticleORM
from src.database.repositories import BaseRepository
from src.domain.models.wb_article import WbArticle


class WbArticleRepository(BaseRepository):
    async def get_list_by_template_id(self, template_id: int) -> list[WbArticle]:
        query = select(WbArticleORM).where(WbArticleORM.template_id == template_id)
        result = await self.session.execute(query)

        wb_articles = result.scalars().all()

        if not wb_articles:
            return []

        return [WbArticle.model_validate(wb_article) for wb_article in wb_articles]
