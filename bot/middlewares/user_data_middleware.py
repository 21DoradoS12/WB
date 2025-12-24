import logging
from typing import Callable, Dict, Any, Awaitable, Union

from aiogram import BaseMiddleware
from aiogram.types import User, CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import UserORM
from src.database.uow import UnitOfWork

log = logging.getLogger(__name__)


class UserDataMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[
            [Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]
        ],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any],
    ) -> Any:
        # Проверяем, есть ли пользователь в событии
        telegram_user = event.from_user

        uow: UnitOfWork = data["uow"]
        session = uow.session

        user = await self.get_or_create_user(session, telegram_user)

        if user:
            await self.update_user_if_needed(session, user, telegram_user)

        data["user"] = user

        return await handler(event, data)

    @staticmethod
    async def get_or_create_user(session: AsyncSession, telegram_user: User) -> UserORM:
        """Получает пользователя из БД или создаёт нового."""
        user = await session.scalar(
            select(UserORM).where(UserORM.id == telegram_user.id)
        )

        if not user:
            log.info(
                f"Регистрация пользователя: ID=%s, username=%s, name=%s",
                telegram_user.id,
                telegram_user.username,
                telegram_user.full_name,
            )
            user = UserORM(
                id=telegram_user.id,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                username=telegram_user.username,
            )
            session.add(user)
            await session.commit()
            log.debug(f"Пользователь %s успешно зарегистрирован", telegram_user.id)

        return user

    @staticmethod
    async def update_user_if_needed(
        session: AsyncSession, user: UserORM, telegram_user: User
    ) -> None:
        """Обновляет поля пользователя, если данные в Telegram были обновлены."""
        fields_to_update = {
            "first_name": telegram_user.first_name,
            "last_name": telegram_user.last_name,
            "username": telegram_user.username,
        }

        needs_update = False

        for field, value in fields_to_update.items():
            if getattr(user, field) != value:
                setattr(user, field, value)
                needs_update = True

        if needs_update:
            log.info(f"Обновление данных пользователя: ID=%s", telegram_user.id)
            await session.commit()
            log.debug(f"Данные пользователя %s успешно обновлены", telegram_user.id)
