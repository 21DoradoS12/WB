from typing import List, TYPE_CHECKING

from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.base import Base
from src.core.database.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.database.models import MaterialORM


class UserORM(TimestampMixin, Base):
    """
    ORM-модель пользователя системы
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True)
    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=True)
    username: Mapped[str] = mapped_column(nullable=True)

    materials: Mapped[List["MaterialORM"]] = relationship(
        back_populates="user",
    )
