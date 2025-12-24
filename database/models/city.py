from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.base import Base

if TYPE_CHECKING:
    from src.database.models import CountryORM


class CityORM(Base):
    __tablename__ = "city"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("country.id"))
    region: Mapped[str]
    name: Mapped[str]
    utc_offset: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    country: Mapped["CountryORM"] = relationship(
        back_populates="cities",
    )
