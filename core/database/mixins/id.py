from sqlalchemy.orm import Mapped, mapped_column


class IDMixin:
    """
    Добавляет стандартное поле id (автоинкрементный первичный ключ)
    """

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
