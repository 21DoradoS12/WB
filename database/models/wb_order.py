from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.base import Base
from src.core.database.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.database.models import WbAssemblyTaskORM, MaterialORM


class WbOrderORM(TimestampMixin, Base):
    """
    ORM-модель вб заказа
    """

    __tablename__ = "wb_orders"

    id: Mapped[str] = mapped_column(primary_key=True)
    region_name: Mapped[str]
    supplier_article: Mapped[str]
    country_name: Mapped[str]
    nm_id: Mapped[int] = mapped_column(BigInteger)
    is_cancel: Mapped[bool]
    warehouse_name: Mapped[str] = mapped_column(nullable=True)
    warehouse_type: Mapped[str] = mapped_column(nullable=True)
    cancel_date: Mapped[datetime] = mapped_column(nullable=True)
    material_id: Mapped[int] = mapped_column(
        ForeignKey(
            "materials.id",
            ondelete="CASCADE",
        ),
        nullable=True,
    )
    material: Mapped["MaterialORM"] = relationship(
        back_populates="wb_orders",
    )
    assembly_task: Mapped["WbAssemblyTaskORM"] = relationship(back_populates="wb_order")
