from aiogram import Router

from . import search, rep


def register_routers() -> Router:
    router = Router()

    router.include_router(search.router)
    router.include_router(rep.router)

    return router
