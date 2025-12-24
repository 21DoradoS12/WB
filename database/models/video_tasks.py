import enum

from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.base import Base
from src.core.database.mixins import IDMixin, TimestampMixin


class VideoStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    error = "error"


class VideoTaskORM(IDMixin, TimestampMixin, Base):
    __tablename__ = "video_tasks"

    params: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped["VideoStatus"] = mapped_column(default=VideoStatus.pending)
    result_path: Mapped[int] = mapped_column(nullable=True)
