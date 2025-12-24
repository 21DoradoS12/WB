from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column

from src.core.database.base import Base
from src.core.database.mixins import IDMixin

if TYPE_CHECKING:
    from src.database.models import TemplateORM


class WbArticleORM(IDMixin, Base):
    __tablename__ = "wb_articles"

    wb_article: Mapped[int]

    template_id: Mapped[int] = mapped_column(ForeignKey("templates.id"))
    template: Mapped["TemplateORM"] = relationship(back_populates="articles")
