from aiogram import Router

from . import order_search


def register_routers() -> Router:
    router = Router()

    router.include_router(order_search.router)

    return router
