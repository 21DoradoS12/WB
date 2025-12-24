from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.core.database.base import Base

if TYPE_CHECKING:
    from src.database.models import WbOrderORM, SupplyORM


class WbAssemblyTaskORM(Base):
    """Модель Задания по сборке заказа wildberries"""

    __tablename__ = "wb_assembly_task"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    wb_order_id: Mapped[str] = mapped_column(ForeignKey("wb_orders.id"))
    created_at: Mapped[datetime]

    wb_order: Mapped["WbOrderORM"] = relationship(back_populates="assembly_task")

    supply_id: Mapped[str] = mapped_column(
        ForeignKey(
            "supplies.id",
            ondelete="CASCADE",
        ),
        nullable=True,
    )
    supply: Mapped["SupplyORM"] = relationship(
        back_populates="assembly_tasks",
    )

    added_to_supply_at: Mapped[datetime] = mapped_column(nullable=True)
