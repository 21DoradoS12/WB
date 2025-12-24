from datetime import date

from sqlalchemy import func, Date
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.base import Base
from src.core.database.mixins import IDMixin


class CategorySupplyCounterORM(IDMixin, Base):
    __tablename__ = "category_supply_counter"

    # Используем mapped_column для правильной аннотации столбца
    category_name: Mapped[str] = mapped_column(nullable=False)
    supply_count: Mapped[int] = mapped_column(default=0)

    # Для даты используем SQLAlchemy Date тип и server_default
    date: Mapped[date] = mapped_column(Date, server_default=func.current_date())
