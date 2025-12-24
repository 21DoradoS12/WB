from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.base import Base

if TYPE_CHECKING:
    from src.database.models import CityORM


class CountryORM(Base):
    __tablename__ = "country"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    utc_offset: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    cities: Mapped[list["CityORM"]] = relationship(
        back_populates="country",
    )
