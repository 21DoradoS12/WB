from src.core.models.base import BaseModelWithConfig


class WbArticleDTO(BaseModelWithConfig):
    id: int
    wb_article: int
    template_id: int
