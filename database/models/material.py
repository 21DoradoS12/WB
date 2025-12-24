from typing import TYPE_CHECKING, List

from sqlalchemy import JSON, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.testing.schema import mapped_column

from src.core.database.base import Base
from src.core.database.mixins import IDMixin, TimestampMixin

if TYPE_CHECKING:
    from src.database.models import UserORM, OrderSearchORM, WbOrderORM


class MaterialORM(IDMixin, TimestampMixin, Base):
    __tablename__ = "materials"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE")
    )
    user: Mapped["UserORM"] = relationship(
        back_populates="materials",
    )

    template_id: Mapped[int] = mapped_column(
        ForeignKey("templates.id", ondelete="CASCADE")
    )
    data: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(default="draft")

    searches: Mapped["OrderSearchORM"] = relationship(
        back_populates="material",
    )

    wb_orders: Mapped[List["WbOrderORM"]] = relationship(
        back_populates="material",
    )
