from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.base import Base
from src.core.database.mixins import TimestampMixin, IDMixin

if TYPE_CHECKING:
    from src.database.models import TemplateORM, CategorySettingsORM


class CategoryORM(IDMixin, TimestampMixin, Base):
    __tablename__ = "categories"

    name: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    folder_name: Mapped[str] = mapped_column(nullable=True)
    save_as_format: Mapped[str] = mapped_column(nullable=True, default="png")

    templates: Mapped["TemplateORM"] = relationship(
        back_populates="category",
    )
    settings: Mapped["CategorySettingsORM"] = relationship(back_populates="category")
