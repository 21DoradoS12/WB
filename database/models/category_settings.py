from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing_extensions import TYPE_CHECKING

from src.core.database.base import Base

if TYPE_CHECKING:
    from src.database.models import CategoryORM


class CategorySettingsORM(Base):
    __tablename__ = "category_settings"

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), primary_key=True
    )
    save_as_format: Mapped[str] = mapped_column(default="png")
    output_path: Mapped[str] = mapped_column(nullable=False)
    save_original_data: Mapped[str] = mapped_column(default=True)

    category: Mapped["CategoryORM"] = relationship(back_populates="settings")
