from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.base import Base
from src.core.database.mixins import TimestampMixin, IDMixin

if TYPE_CHECKING:
    from src.database.models import CategoryORM, WbArticleORM


class TemplateORM(IDMixin, TimestampMixin, Base):
    __tablename__ = "templates"

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    category: Mapped["CategoryORM"] = relationship(
        back_populates="templates",
    )

    name: Mapped[str]
    template_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    photo: Mapped[str] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(nullable=True)
    form_steps: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    articles: Mapped["WbArticleORM"] = relationship(
        back_populates="template",
    )
