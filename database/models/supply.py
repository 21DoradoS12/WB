from typing import TYPE_CHECKING, List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.base import Base
from src.core.database.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.database.models import WbAssemblyTaskORM


class SupplyORM(TimestampMixin, Base):
    __tablename__ = "supplies"

    id: Mapped[str] = mapped_column(primary_key=True)
    category_name: Mapped[str]
    name: Mapped[str]
    order_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(default="active", nullable=True)

    assembly_tasks: Mapped[List["WbAssemblyTaskORM"]] = relationship(
        back_populates="supply",
    )
