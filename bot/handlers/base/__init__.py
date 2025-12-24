from aiogram import Router

from . import (
    start,
)


def register_routers() -> Router:
    router = Router()

    router.include_router(start.router)

    return router
