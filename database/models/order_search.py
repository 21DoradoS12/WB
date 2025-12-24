from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.base import Base
from src.core.database.mixins import TimestampMixin, IDMixin
from src.core.enums.order_search import OrderSearchStatus

if TYPE_CHECKING:
    from src.database.models import MaterialORM


class OrderSearchORM(IDMixin, TimestampMixin, Base):
    __tablename__ = "order_search"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    material: Mapped["MaterialORM"] = relationship(
        back_populates="searches",
    )

    search_type: Mapped[str]
    filters: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(default=OrderSearchStatus.PENDING)
    last_checked_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        server_onupdate=func.now(),
    )
