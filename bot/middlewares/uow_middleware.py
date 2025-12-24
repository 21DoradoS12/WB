from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.database.uow import UnitOfWork


class UnitOfWorkMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Работа с UnitOfWork
        """
        async with UnitOfWork() as uow:
            data["uow"] = uow
            data = await handler(event, data)

        return data
