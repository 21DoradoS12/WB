from aiogram import Router

from src.bot.filters.is_manager_filter import IsManagerInChat
from . import material, cancel, order, supply


def register_routers() -> Router:
    router = Router()
    router.message.filter(IsManagerInChat())

    router.callback_query.filter(IsManagerInChat())

    router.include_router(material.register_routers())
    router.include_router(order.register_routers())
    router.include_router(supply.register_routers())
    router.include_router(cancel.router)

    return router
